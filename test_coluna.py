#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar se a correção da coluna 'usuario' funcionou
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from bot_oab_supabase import SupabaseConnector

def testar_coluna_usuario():
    """Testa se a coluna 'usuario' está sendo acessada corretamente"""
    
    print("🔧 Testando correção da coluna 'usuario'...")
    print("=" * 50)
    
    # Verificar configuração
    print(f"📋 Coluna configurada: {Config.COLUNA_USUARIOS}")
    
    # Testar conexão
    try:
        supabase = SupabaseConnector(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        
        # Testar consulta simples
        print("🔍 Testando consulta na coluna 'usuario'...")
        response = supabase.client.table('erros_processados').select('id, usuario').limit(3).execute()
        
        if response.data:
            print(f"✅ Consulta bem-sucedida! Encontrados {len(response.data)} registros:")
            for item in response.data:
                print(f"   ID: {item['id']} | Usuario: {item['usuario']}")
        else:
            print("⚠️ Nenhum registro encontrado")
        
        # Testar busca de registros pendentes
        print("\n🔍 Testando busca de registros pendentes...")
        registros_pendentes = supabase.buscar_registros_pendentes()
        
        print(f"📊 Registros pendentes encontrados: {len(registros_pendentes)}")
        
        if registros_pendentes:
            print("✅ Primeiros registros pendentes:")
            for i, registro in enumerate(registros_pendentes[:3], 1):
                print(f"   {i}. ID: {registro.id} | Usuario: {registro.usuario}")
        
        print("\n🎉 Teste concluído com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        print("\n💡 Verifique se:")
        print("   1. Todas as modificações foram aplicadas")
        print("   2. A coluna no banco realmente se chama 'usuario'")
        print("   3. As credenciais estão corretas")

if __name__ == "__main__":
    testar_coluna_usuario()