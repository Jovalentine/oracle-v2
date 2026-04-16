import os
import json
import time
from google import genai
from google.genai import types
from PIL import Image
from core.video_utils import extract_keyframes

class GeminiForensicPipeline:
    def __init__(self):
        # Fallback to KEY_1 if the general GEMINI_API_KEY is not set
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY_1")
        if not api_key:
            raise ValueError("GEMINI_API_KEY_1 is not set in the .env file.")
        
        # Default client for standard uploads (Image/Video Dashboard)
        self.default_client = genai.Client(api_key=api_key)
        
        # YOUR MODEL FALLBACK CHAIN (Updated for Gemini 2.5)
        self.model_priority = [
            'gemini-2.5-flash',       # 1. First choice (High performance)
            'gemini-2.5-flash-lite',  # 2. Fast/Lower demand fallback
            'gemini-2.5-pro',         # 3. Heavy lifting fallback
            'gemini-2.0-flash'        # 4. Ultra-stable last resort
        ]
        
        # Model fallback chain for IMAGE analysis
        self.image_models = self.model_priority
        
        # Model fallback chain for VIDEO analysis (only models that support generateContent)
        self.video_models = self.model_priority

        # Lower safety thresholds for Forensic Analysis
        self.safety = [
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_ONLY_HIGH",
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_ONLY_HIGH",
            )
        ]

    def _parse_response(self, response) -> dict:
        """Safely extracts JSON, handling safety blocks and markdown formatting."""
        try:
            raw_text = response.text
        except ValueError:
            print("⚠️ SAFETY BLOCK: Gemini refused to process this image.")
            return {
                "scene_summary": "⚠️ AI SECURITY BLOCK: The evidence was flagged by Gemini's safety filters as too graphic or violent.",
                "severity_score": 0,
                "collision_type": "Safety Blocked",
                "pedestrians_detected": False,
                "license_plates_detected": [],
                "vehicles_involved": [],
                "investigative_narrative": "The AI refused to analyze this evidence due to safety constraints. Try a less graphic angle."
            }

        if raw_text.startswith("```"):
            raw_text = raw_text.strip("` \n")
            if raw_text.startswith("json"):
                raw_text = raw_text[4:].strip()

        try:
            result_dict = json.loads(raw_text)
            print("\n✅ --- GEMINI AI RAW OUTPUT ---")
            print(json.dumps(result_dict, indent=2))
            print("------------------------------\n")
            
            if "scene_summary" not in result_dict:
                for val in result_dict.values():
                    if isinstance(val, dict) and "scene_summary" in val:
                        return val
            return result_dict
        except json.JSONDecodeError as e:
            print(f"❌ JSON PARSE ERROR. Raw output was:\n{raw_text}")
            raise e

    def analyze_image(self, image_path: str, api_key: str = None) -> dict:
        """Analyzes a single accident image with Model Fallback logic."""
        try:
            img = Image.open(image_path)
        except Exception as e:
            raise FileNotFoundError(f"Could not open image: {e}")

        client = genai.Client(api_key=api_key) if api_key else self.default_client

        prompt = """
        You are an expert digital forensic investigator analyzing a traffic accident scene.
        Carefully analyze this image and output a strict JSON object with the following schema exactly:
        {
            "scene_summary": "A detailed 1-2 sentence caption of the accident scene.",
            "collision_type": "Head-on, Rear-end, Side-impact, Rollover, or N/A",
            "severity_score": <integer from 0 to 100>,
            "pedestrians_detected": <boolean>,
            "license_plates_detected": ["List", "of", "plates", "if", "visible", "otherwise empty"],
            "vehicles_involved": [
                {
                    "type": "car/truck/motorcycle/bus/etc",
                    "fault_percentage": <integer from 0 to 100>,
                    "reasoning": "Investigative reasoning for this fault assignment based on position and damage."
                }
            ],
            "investigative_narrative": "A professional, 2-paragraph forensic reconstruction of the event."
        }
        """
        
        # TRY EACH IMAGE MODEL IN THE CHAIN
        for model_id in self.image_models:
            try:
                print(f"🕵️ Attempting image analysis with: {model_id}")
                response = client.models.generate_content(
                    model=model_id,
                    contents=[img, prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2,
                        safety_settings=self.safety
                    ),
                )
                return self._parse_response(response)
            except Exception as e:
                error_str = str(e)
                if any(code in error_str for code in ["503", "429", "404"]):
                    print(f"⚠️ {model_id} is not available (busy or not supported). Trying next fallback model...")
                    time.sleep(1)
                    continue
                else:
                    raise e
        return {"error": "All models in the fallback chain are currently unavailable."}

    def analyze_video(self, video_path: str, api_key: str = None) -> dict:
        """Extracts keyframes and reconstructs the timeline with Model Fallback logic."""
        try:
            print(f"🎥 Extracting keyframes from {video_path}...")
            frames, fps = extract_keyframes(video_path, max_frames=15)
        except Exception as e:
            raise RuntimeError(f"Video extraction failed: {e}")

        client = genai.Client(api_key=api_key) if api_key else self.default_client

        prompt = """
        You are an expert digital forensic investigator analyzing an accident dashcam or CCTV video.
        I have provided a sequence of chronological frames extracted from the video.
        Carefully analyze the sequence to reconstruct the event and output a strict JSON object with this exact schema:
        {
            "scene_summary": "A detailed 2-sentence caption of the entire video sequence.",
            "collision_type": "Head-on, Rear-end, Side-impact, Rollover, or N/A",
            "severity_score": <integer from 0 to 100>,
            "pedestrians_detected": <boolean>,
            "license_plates_detected": ["List", "of", "plates", "if", "visible", "otherwise empty"],
            "vehicles_involved": [
                {
                    "type": "car/truck/motorcycle/bus/etc",
                    "fault_percentage": <integer from 0 to 100>,
                    "reasoning": "Investigative reasoning for this fault assignment based on motion and impact."
                }
            ],
            "investigative_narrative": "A professional, 2-paragraph forensic reconstruction of the event.",
            "timeline": [
                {
                    "timestamp_sec": "<approximate second, e.g., '0.0', '1.5'>",
                    "event": "Description of what happens at this moment (e.g., 'Impact occurs')"
                }
            ]
        }
        """
        
        # TRY EACH VIDEO MODEL IN THE CHAIN
        for model_id in self.video_models:
            try:
                print(f"🎥 Attempting video analysis with: {model_id}")
                contents = frames + [prompt]
                
                response = client.models.generate_content(
                    model=model_id,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2,
                        safety_settings=self.safety
                    ),
                )
                
                result_dict = self._parse_response(response)
                result_dict["video_meta"] = {"fps": round(fps, 1), "frames_analyzed": len(frames), "model_used": model_id}
                return result_dict
            except Exception as e:
                error_str = str(e)
                if any(code in error_str for code in ["503", "429", "404"]):
                    print(f"⚠️ {model_id} is not available (busy or not supported). Trying next fallback model...")
                    time.sleep(2)
                    continue
                raise e
        return {"error": "Video forensic analysis failed on all models in the fallback chain."}