"""
角色数据工具模块
包含角色数据加载和处理的工具函数
"""

import os
import re

def load_character_data():
    """加载所有角色的音频数据"""
    character_data = {}
    reference_audios_path = "reference_audios"
    
    if not os.path.exists(reference_audios_path):
        return character_data
    
    # 加载emotions目录
    emotions_path = os.path.join(reference_audios_path, "emotions")
    if os.path.exists(emotions_path):
        for character_name in os.listdir(emotions_path):
            character_dir = os.path.join(emotions_path, character_name)
            if os.path.isdir(character_dir):
                if character_name not in character_data:
                    character_data[character_name] = {"emotions": {}, "randoms": {}}
                
                # 遍历语言目录
                for lang_dir in os.listdir(character_dir):
                    lang_path = os.path.join(character_dir, lang_dir)
                    if os.path.isdir(lang_path):
                        character_data[character_name]["emotions"][lang_dir] = []
                        
                        # 加载音频文件
                        for audio_file in os.listdir(lang_path):
                            if audio_file.endswith('.wav'):
                                # 从文件名提取情感和文本
                                match = re.match(r'【(.+?)】(.+)\.wav', audio_file)
                                if match:
                                    emotion = match.group(1)
                                    text = match.group(2)
                                    audio_path = os.path.join(lang_path, audio_file)
                                    character_data[character_name]["emotions"][lang_dir].append({
                                        "emotion": emotion,
                                        "text": text,
                                        "path": audio_path,
                                    })
    
    # 加载randoms目录
    randoms_path = os.path.join(reference_audios_path, "randoms")
    if os.path.exists(randoms_path):
        for character_name in os.listdir(randoms_path):
            character_dir = os.path.join(randoms_path, character_name)
            if os.path.isdir(character_dir):
                if character_name not in character_data:
                    character_data[character_name] = {"emotions": {}, "randoms": {}}
                
                # 遍历语言目录
                for lang_dir in os.listdir(character_dir):
                    lang_path = os.path.join(character_dir, lang_dir)
                    if os.path.isdir(lang_path):
                        character_data[character_name]["randoms"][lang_dir] = []
                        
                        # 加载音频和lab文件对
                        wav_files = [f for f in os.listdir(lang_path) if f.endswith('.wav')]
                        for wav_file in wav_files:
                            lab_file = wav_file.replace('.wav', '.lab')
                            lab_path = os.path.join(lang_path, lab_file)
                            wav_path = os.path.join(lang_path, wav_file)
                            
                            if os.path.exists(lab_path):
                                try:
                                    with open(lab_path, 'r', encoding='utf-8') as f:
                                        text = f.read().strip()
                                    
                                    character_data[character_name]["randoms"][lang_dir].append({
                                        "text": text,
                                        "path": wav_path,
                                    })
                                except Exception as e:
                                    print(f"Error reading lab file {lab_path}: {e}")
    
    return character_data

def get_default_happy_audio(character_name, character_data, language="中文"):
    """获取角色的默认开心音频"""
    if character_name in character_data and language in character_data[character_name]["emotions"]:
        for audio_info in character_data[character_name]["emotions"][language]:
            if "开心" in audio_info["emotion"] or "happy" in audio_info["emotion"]:
                return audio_info
        # 如果没有开心音频，返回第一个emotions音频
        if character_data[character_name]["emotions"][language]:
            return character_data[character_name]["emotions"][language][0]
    
    # 如果emotions中没有音频，尝试randoms
    if character_name in character_data and language in character_data[character_name]["randoms"]:
        if character_data[character_name]["randoms"][language]:
            return character_data[character_name]["randoms"][language][0]
    
    return None 