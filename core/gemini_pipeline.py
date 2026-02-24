import os
import json
from google import genai
from google.genai import types
from PIL import Image
from core.video_utils import extract_keyframes

class GeminiForensicPipeline:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in the .env file.")
        
        self.client = genai.Client(api_key=api_key)
        self.model_id = 'gemini-2.5-flash' 

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
            # If safety filter blocked it, accessing .text throws a ValueError
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

        # Clean markdown formatting if Gemini wrapped it
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("` \n")
            if raw_text.startswith("json"):
                raw_text = raw_text[4:].strip()

        try:
            result_dict = json.loads(raw_text)
            
            # Print to terminal so you can see exactly what the AI found!
            print("\n✅ --- GEMINI AI RAW OUTPUT ---")
            print(json.dumps(result_dict, indent=2))
            print("------------------------------\n")
            
            # Failsafe: if Gemini nested the JSON inside a "response" key
            if "scene_summary" not in result_dict:
                for val in result_dict.values():
                    if isinstance(val, dict) and "scene_summary" in val:
                        return val
                        
            return result_dict
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON PARSE ERROR. Raw output was:\n{raw_text}")
            raise e

    def analyze_image(self, image_path: str) -> dict:
        """Analyzes a single accident image."""
        try:
            img = Image.open(image_path)
        except Exception as e:
            raise FileNotFoundError(f"Could not open image: {e}")

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
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=[img, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
                safety_settings=self.safety
            ),
        )
        return self._parse_response(response)

    def analyze_video(self, video_path: str) -> dict:
        """Extracts keyframes from a video and asks Gemini to reconstruct the timeline."""
        try:
            print(f"🎥 Extracting keyframes from {video_path}...")
            frames, fps = extract_keyframes(video_path, max_frames=15)
        except Exception as e:
            raise RuntimeError(f"Video extraction failed: {e}")

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
        
        print(f"⏳ Sending {len(frames)} frames to Gemini API...")
        contents = frames + [prompt]
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
                safety_settings=self.safety
            ),
        )
        
        result_dict = self._parse_response(response)
        result_dict["video_meta"] = {"fps": round(fps, 1), "frames_analyzed": len(frames)}
        return result_dict