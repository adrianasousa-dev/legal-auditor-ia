# -*- coding: utf-8 -*-
"""
M.A | JUS IA EXPERIENCE - Auditoria Criminal (Parecer Premium)
Aplicação Desktop de Alta Performance para Engenharia Jurídica.
Orquestração de LLMs com Escudos Anti-Alucinação via Regex.
Autor: Adriana Sousa
"""

import os
import json
import time
import datetime
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import docx
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from google import genai
from google.genai import types
import re 
from dotenv import load_dotenv

# --- PROTOCOLO DE SEGURANÇA ---
# Carrega as variáveis do ficheiro .env local para evitar exposição de chaves
load_dotenv()

# ==========================================
# MOTOR DE BUSCA WEB (DUCKDUCKGO)
# ==========================================
try:
    from duckduckgo_search import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False

# CONFIGURAÇÃO DE SEGURANÇA: A chave é lida do ambiente, nunca escrita no código.
API_KEY_ENV = os.getenv("GEMINI_API_KEY", "")

# ==========================================
# O ESCUDO DE CÓDIGO (REGEX) - A PORTA DE AÇO
# ==========================================
def escudo_anti_alucinacao(texto):
    """
    Filtra e mascara numerações de processos e jurisprudências para evitar 
    que a IA gere dados fictícios (alucinações).
    """
    padrao_jurisprudencia = r'(?i)\b(?:HC|Habeas Corpus|REsp|Recurso Especial|RHC|AgRg|AREsp|Apelação|Agravo|Processo)\s*(?:n[º°]?\s*)?[\d\.\-\/]+\/[A-Z]{2}\b'
    texto_limpo = re.sub(padrao_jurisprudencia, "[AVISO: NUMERAÇÃO OMITIDA PELO ESCUDO - CONSULTE FONTE OFICIAL]", texto)
    return texto_limpo

def buscar_jurisprudencia_real(foco_busca):
    """Realiza busca tática web para fornecer contexto real à IA."""
    if not HAS_DDGS: return "Busca web indisponível."
    try:
        termo = f"{foco_busca} penal processo penal jurisprudencia 2025 site:jusbrasil.com.br"
        resultados = DDGS().text(termo, max_results=3)
        texto_pesquisa = "\n".join([f"- {r['title']}: {r['body']}" for r in resultados])
        return texto_pesquisa if texto_pesquisa else "Nenhuma jurisprudência localizada online."
    except Exception:
        return "Serviço de busca temporariamente indisponível."

# ==========================================
# LÓGICA DE AUDITORIA EM LOTE (IA)
# ==========================================
def analisar_lote_ia(caminhos_txt, fatos, callback_progresso, callback_sucesso, callback_erro):
    try:
        if not API_KEY_ENV:
            raise Exception("ERRO DE SEGURANÇA: GEMINI_API_KEY não encontrada no ficheiro .env")

        client = genai.Client(api_key=API_KEY_ENV.strip())
        
        filtros_seguranca = [
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
        ]

        # FASE 0: BUSCA DE CONTEXTO REAL
        callback_progresso(0, len(caminhos_txt) + 1, "Pesquisando teses reais no Jusbrasil...")
        contexto_web = buscar_jurisprudencia_real(fatos)

        resumos_volumes = []
        total_vols = len(caminhos_txt)

        for idx, caminho in enumerate(caminhos_txt):
            vol_num = idx + 1
            callback_progresso(vol_num, total_vols + 1, f"Fase 1: Auditando Volume {vol_num}...")
            
            # Upload e Processamento
            gemini_file = client.files.upload(file=caminho, config={'mime_type': 'text/plain'})
            while True:
                f_info = client.files.get(name=gemini_file.name)
                if "ACTIVE" in str(f_info.state).upper(): break
                time.sleep(2)
            
            conteudo_txt = types.Part.from_uri(file_uri=f_info.uri, mime_type='text/plain')
            
            prompt_detetive = f"DIRECIONAMENTO DA ESTRATÉGIA:\n{fatos}\n\nAnalise este volume Criminal. Foque em autoria, materialidade e nulidades processuais (buscas ilegais, etc). CITE AS FLS. Não invente dados."
            config_detetive = types.GenerateContentConfig(temperature=0.1, safety_settings=filtros_seguranca)
            response_detetive = client.models.generate_content(model='gemini-2.5-flash', contents=[conteudo_txt, prompt_detetive], config=config_detetive)
            
            resumos_volumes.append(f"--- ACHADOS DO VOLUME {vol_num} ---\n{response_detetive.text.strip()}\n")
            client.files.delete(name=gemini_file.name)

        # FASE FINAL: CONSOLIDAÇÃO PREMIUM
        callback_progresso(total_vols, total_vols + 1, "Fase 2: Estruturando Parecer Premium...")
        texto_consolidado = "\n".join(resumos_volumes)

        instrucao_sistema = """
        Você é o M.A | JUS IA EXPERIENCE, um Auditor Forense Criminal.
        Sua missão é gerar um PARECER PREMIUM denso, dissertativo e de alta complexidade.
        Responda obrigatoriamente no formato JSON estruturado.
        """
        
        prompt_mestre = f"DIRECIONAMENTO:\n{fatos}\n\n--- DADOS COLETADOS ---\n{texto_consolidado}\n\n--- PESQUISA REAL ---\n{contexto_web}\n\nGere o Parecer em JSON."

        config_mestre = types.GenerateContentConfig(system_instruction=instrucao_sistema, temperature=0.2, safety_settings=filtros_seguranca)
        response_final = client.models.generate_content(model='gemini-2.5-flash', contents=[prompt_mestre], config=config_mestre)

        # Aplicação do Escudo Anti-Alucinação no output final
        texto_puro = response_final.text.strip()
        texto_limpo = escudo_anti_alucinacao(texto_puro)
        
        # Limpeza de markdown do JSON
        if texto_limpo.startswith("
