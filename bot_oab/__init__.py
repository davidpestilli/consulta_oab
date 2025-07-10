#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot OAB - Pacote principal
"""

from .models.resultado_oab import ResultadoOAB
from .core.bot_oab_core import BotOABCorrigido
from .config.browser_config import BrowserConfig
from .extractors.data_extractors import DataExtractor, ModalExtractorGenerico, ModalExtractorOCR
from .utils.data_exporters import DataExporter

__all__ = [
    'ResultadoOAB',
    'BotOABCorrigido', 
    'BrowserConfig',
    'DataExtractor',
    'ModalExtractorGenerico',
    'ModalExtractorOCR',
    'DataExporter'
]