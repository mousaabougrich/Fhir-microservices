import os
import base64
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

import httpx
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Load environment variables
load_dotenv()

from featurizer.models import PatientFeatures

logger = logging.getLogger("featurizer")


class FeaturizerService:
    """Core featurizer: fetch de-identified resources, extract structured features,
    decode attachments and produce simple NLP embeddings/tags.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: int = 30, db_session: Optional[Session] = None):
        self.base_url = base_url or os.getenv("DEID_BASE_URL", "http://deid:8000")
        self.client = httpx.Client(timeout=timeout)
        self.db = db_session

        # choose embedding backend; by default use sentence-transformers (small)
        self.use_biobert = os.getenv("USE_BIOBERT", "false").lower() in ("1", "true", "yes")
        self.embedding_backend = None
        self._init_embedding()

    def _init_embedding(self):
        if self.use_biobert:
            try:
                from transformers import AutoTokenizer, AutoModel
                import torch

                self._tok = AutoTokenizer.from_pretrained("dmis-lab/biobert-base-cased-v1.1")
                self._model = AutoModel.from_pretrained("dmis-lab/biobert-base-cased-v1.1")
                self.embedding_backend = "biobert"
                logger.info("Using BioBERT for embeddings")
                return
            except Exception as e:
                logger.warning("BioBERT init failed: %s; falling back", e)

        try:
            from sentence_transformers import SentenceTransformer

            self._st = SentenceTransformer("all-MiniLM-L6-v2")
            self.embedding_backend = "sbert"
            logger.info("Using sentence-transformers (all-MiniLM-L6-v2)")
        except Exception as e:
            logger.warning("No embedding backend available: %s", e)
            self.embedding_backend = None

    def _get(self, path: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/') }"
        r = self.client.get(url)
        r.raise_for_status()
        return r.json()

    def fetch_resources_for_patient(self, patient_id: str) -> Dict[str, List[Dict[str, Any]]]:
        endpoints = [
            "deid/patients",
            "deid/encounters",
            "deid/conditions",
            "deid/observations",
            "deid/medication-requests",
            "deid/diagnostic-reports",
            "deid/document-references",
        ]
        resources: Dict[str, List[Dict[str, Any]]] = {}
        for ep in endpoints:
            try:
                data = self._get(ep)
                # allow either plain list or wrapper dict
                items = data if isinstance(data, list) else list(data.values())[0] if isinstance(data, dict) else []
                filtered = [i for i in items if i.get("patient_resource_id") == patient_id]
                resources[ep.split('/')[-1]] = filtered
            except Exception as e:
                logger.warning("Failed fetching %s: %s", ep, e)
                resources[ep.split('/')[-1]] = []

        return resources

    def _decode_attachments(self, doc_refs: List[Dict[str, Any]]) -> List[str]:
        notes: List[str] = []
        for dr in doc_refs:
            att_data = dr.get("attachment_data")
            # fallback to parsing raw_fhir_data if needed
            if not att_data:
                raw = dr.get("raw_fhir_data")
                if raw:
                    try:
                        import json

                        raw_obj = json.loads(raw)
                        content = raw_obj.get("content", [])
                        if content:
                            a = content[0].get("attachment", {})
                            att_data = a.get("data")
                    except Exception:
                        pass

            if not att_data:
                continue

            try:
                text = base64.b64decode(att_data).decode("utf-8", errors="replace")
                notes.append(text)
            except Exception:
                notes.append(att_data)

        return notes

    def extract_structured_features(self, resources: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        patients = resources.get("patients", [])
        if patients:
            p = patients[0]
            out["gender"] = p.get("gender")
            out["birth_date"] = p.get("birth_date")
            out["state"] = p.get("state")

        encs = resources.get("encounters", [])
        out["num_encounters"] = len(encs)
        if encs:
            los = [e.get("length_of_stay_days") or 0 for e in encs]
            out["avg_los"] = float(np.mean(los)) if los else 0.0

        conds = resources.get("conditions", [])
        out["num_conditions"] = len(conds)

        meds = resources.get("medication-requests", [])
        out["num_med_requests"] = len(meds)

        obs = resources.get("observations", [])
        abnormal = 0
        for o in obs:
            if o.get("value_string") and any(k in str(o.get("value_string")).lower() for k in ("high", "low", "abnormal")):
                abnormal += 1
        out["obs_abnormal_count"] = abnormal

        return out

    def _run_spacy_ner(self, texts: List[str]) -> List[Dict[str, Any]]:
        try:
            import spacy
            try:
                nlp = spacy.load("en_core_sci_md")
            except Exception:
                nlp = spacy.load("en_core_web_sm")

            entities = []
            for t in texts:
                doc = nlp(t)
                for ent in doc.ents:
                    entities.append({"text": ent.text, "label": ent.label_})
            return entities
        except Exception as e:
            logger.warning("spaCy unavailable: %s", e)
            return []

    def _get_embeddings(self, texts: List[str]) -> Optional[List[List[float]]]:
        if not texts:
            return None
        if self.embedding_backend == "biobert":
            try:
                import torch

                toks = self._tok(texts, return_tensors="pt", padding=True, truncation=True)
                with torch.no_grad():
                    out = self._model(**toks)
                embs = out.last_hidden_state.mean(dim=1).cpu().numpy().tolist()
                return embs
            except Exception as e:
                logger.warning("BioBERT embedding failed: %s", e)
                return None

        if self.embedding_backend == "sbert":
            try:
                embs = self._st.encode(texts, show_progress_bar=False, convert_to_numpy=True)
                return embs.tolist()
            except Exception as e:
                logger.warning("SentenceTransformer failed: %s", e)
                return None

        return None

    def featurize_patient(self, patient_id: str) -> Dict[str, Any]:
        resources = self.fetch_resources_for_patient(patient_id)
        structured = self.extract_structured_features(resources)

        doc_refs = resources.get("document-references", []) or []
        diag_reports = resources.get("diagnostic-reports", []) or []

        texts = self._decode_attachments(doc_refs) + [d.get("conclusion") for d in diag_reports if d.get("conclusion")]
        texts = [t for t in texts if t]

        ner = self._run_spacy_ner(texts)
        emb = self._get_embeddings(texts)

        features = {
            "patient_resource_id": patient_id,
            **structured,
            "ner_entities": ner,
            "embeddings": emb,
        }
        return features

    def featurize_bulk(self, patient_ids: List[str]) -> pd.DataFrame:
        rows = []
        for pid in patient_ids:
            try:
                f = self.featurize_patient(pid)
                # compute mean embedding if available
                if f.get("embeddings"):
                    import numpy as _np

                    mean_emb = _np.mean(_np.array(f.get("embeddings")), axis=0).tolist()
                    f["embedding_mean"] = mean_emb
                else:
                    f["embedding_mean"] = None
                f.pop("embeddings", None)
                rows.append(f)
            except Exception as e:
                logger.exception("Failed patient %s: %s", pid, e)

        return pd.DataFrame(rows)

    def save_features_to_db(self, features: Dict[str, Any]) -> Optional[PatientFeatures]:
        """Save patient features to database if db session is available"""
        if not self.db:
            return None
            
        try:
            # Check if patient already exists
            existing = self.db.query(PatientFeatures).filter(
                PatientFeatures.patient_resource_id == features["patient_resource_id"]
            ).first()
            
            if existing:
                # Update existing record
                for key, value in features.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                patient_features = existing
            else:
                # Create new record
                patient_features = PatientFeatures(**features)
                self.db.add(patient_features)
            
            self.db.commit()
            self.db.refresh(patient_features)
            return patient_features
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error: {e}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Database error: {e}")
            return None

    def get_features_from_db(self, patient_id: str) -> Optional[PatientFeatures]:
        """Get patient features from database if available"""
        if not self.db:
            return None
            
        try:
            return self.db.query(PatientFeatures).filter(
                PatientFeatures.patient_resource_id == patient_id
            ).first()
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return None

    def featurize_patient_with_db(self, patient_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Featurize patient with database caching"""
        # Check database first unless force refresh
        if not force_refresh and self.db:
            cached = self.get_features_from_db(patient_id)
            if cached:
                logger.info(f"Retrieved cached features for patient {patient_id}")
                return cached.to_dict()
        
        # Generate features
        features = self.featurize_patient(patient_id)
        
        # Save to database
        if self.db:
            saved = self.save_features_to_db(features)
            if saved:
                logger.info(f"Saved features for patient {patient_id} to database")
                return saved.to_dict()
        
        return features
