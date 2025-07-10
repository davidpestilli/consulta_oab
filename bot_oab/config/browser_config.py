#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuração e setup do navegador para o Bot OAB
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class BrowserConfig:
    """Classe responsável pela configuração do navegador Chrome"""
    
    @staticmethod
    def setup_driver(headless: bool = False) -> webdriver.Chrome:
        """
        Configura o driver do Chrome
        
        Args:
            headless: Se True, executa sem interface gráfica
            
        Returns:
            Instância configurada do ChromeDriver
        """
        options = Options()
        
        if headless:
            options.add_argument('--headless')
            
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Desabilitar notificações e popups
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
        }
        options.add_experimental_option("prefs", prefs)
        
        driver = webdriver.Chrome(options=options)
        
        # Executar script para remover sinais de webdriver
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver