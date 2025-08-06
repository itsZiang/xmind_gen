import whisper
import subprocess
import sys
import tempfile
import os
import logging
from typing import Optional, Union
from core.llm_handle import translate_to_vietnamese
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)

class WhisperModelManager:
    _instance = None
    _model = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_model(self):
        if self._model is None:
            logger.info("Loading Whisper model...")
            self._model = whisper.load_model("tiny")
            logger.info("Whisper model loaded successfully")
        return self._model

def transcribe_audio_file(file_path: str) -> str:
    try:
        logger.info(f"Starting transcription for file: {file_path}")
        
        if not os.path.exists(file_path):
            raise Exception(f"Audio file not found: {file_path}")
        
        if os.path.getsize(file_path) == 0:
            raise Exception("Audio file is empty")
        
        output_dir = os.path.join("static", "output_audio")
        os.makedirs(output_dir, exist_ok=True)
        
        base_filename = os.path.splitext(os.path.basename(file_path))[0]
        output_file = os.path.join(output_dir, f"{base_filename}.txt")

        model = WhisperModelManager.get_instance().get_model()
        
        try:
            audio = whisper.load_audio(file_path)
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio, n_mels=model.dims.n_mels).to(model.device)
            _, probs = model.detect_language(mel)
            detected_lang = max(probs, key=probs.get)
            logger.info(f"Detected language: {detected_lang}")
        except Exception as lang_error:
            logger.warning(f"Language detection failed: {lang_error}, using auto detection")
            detected_lang = "auto"
        
        cmd = [
            sys.executable, "-m", "whisper",
            file_path,
            "--model", "small",
            "--task", "translate",  
            "--output_dir", output_dir, 
            "--output_format", "txt"
        ]
        
        if detected_lang != "auto":
            cmd.extend(["--language", detected_lang])
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True, 
            text=True, 
            timeout=300
        )
        
        if result.returncode != 0:
            logger.error(f"Whisper CLI stdout: {result.stdout}")
            logger.error(f"Whisper CLI stderr: {result.stderr}")
            raise Exception(f"Whisper transcription failed: {result.stderr}")
        
        if not os.path.exists(output_file):
            txt_files = [f for f in os.listdir(output_dir) if f.endswith('.txt')]
            if txt_files:
                latest_file = max([os.path.join(output_dir, f) for f in txt_files], 
                                key=os.path.getmtime)
                output_file = latest_file
            else:
                logger.error(f"Output file not found at: {output_file}")
                logger.error(f"Directory contents: {os.listdir(output_dir)}")
                raise Exception("Transcription output file not found")
            
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                transcribed_text = f.read().strip()
            
            if not transcribed_text:
                raise Exception("Transcribed text is empty")
                
            logger.info(f"Transcription completed successfully. File saved at: {output_file}")
            logger.info(f"Transcription length: {len(transcribed_text)} characters")
            return transcribed_text
            
        except IOError as e:
            logger.error(f"Error reading output file: {str(e)}")
            raise Exception(f"Failed to read transcription output: {str(e)}")
            
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        raise

def process_uploaded_audio(uploaded_file) -> str:
    tmp_file_path = None
    try:
        file_extension = "wav"  # default
        if hasattr(uploaded_file, 'filename') and uploaded_file.filename:
            file_extension = uploaded_file.filename.split(".")[-1].lower()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as tmp_file:
            if hasattr(uploaded_file, 'file'):
                content = uploaded_file.file.read()
            elif hasattr(uploaded_file, 'read'):
                content = uploaded_file.read()
            else:
                content = uploaded_file
            
            if not content:
                raise Exception("No audio data received")
            
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        logger.info(f"Saved uploaded file to: {tmp_file_path}")
        logger.info(f"File size: {os.path.getsize(tmp_file_path)} bytes")
        
        english_text = transcribe_audio_file(tmp_file_path)
        
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
            tmp_file_path = None
        
        vietnamese_text = translate_to_vietnamese(english_text)
        
        logger.info("Audio processing completed successfully")
        return vietnamese_text
        
    except Exception as e:
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        logger.error(f"Audio processing error: {str(e)}")
        raise e

def validate_audio_file(uploaded_file) -> bool:
    if not uploaded_file:
        logger.warning("No file uploaded")
        return False
    
    if not hasattr(uploaded_file, 'filename') or not uploaded_file.filename:
        logger.warning("File has no filename")
        return False
    
    valid_extensions = ['wav', 'mp3', 'm4a', 'ogg', 'flac', 'aac']
    file_extension = uploaded_file.filename.split('.')[-1].lower()
    
    if file_extension not in valid_extensions:
        logger.warning(f"Invalid audio format: {file_extension}")
        return False
    
    max_size = 25 * 1024 * 1024
    
    if hasattr(uploaded_file, 'size') and uploaded_file.size:
        if uploaded_file.size > max_size:
            logger.warning(f"File too large: {uploaded_file.size} bytes")
            return False
    
    return True