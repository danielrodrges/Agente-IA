"""
Script utilitário para limpar sessões WhatsApp desconectadas.
Use quando houver problemas de reconexão.
"""
import os
import sys
from database import SessionLocal, criar_tabelas
from sessao.sessao_model import Sessao
from config.config_service import ConfiguracaoService

def limpar_sessoes():
    """Limpa todas as sessões desconectadas e seus arquivos."""
    print("🧹 Limpando sessões desconectadas...\n")
    
    # Conectar ao banco
    db = SessionLocal()
    
    try:
        # Obter diretório de sessões configurado
        sessao_dir = ConfiguracaoService.obter_valor(db, "sessao_diretorio", "./sessoes")
        
        # Buscar todas as sessões
        sessoes = db.query(Sessao).all()
        
        if not sessoes:
            print("⚠️  Nenhuma sessão encontrada no banco de dados.")
            return
        
        print(f"📊 Total de sessões no banco: {len(sessoes)}")
        print(f"📁 Diretório de sessões: {sessao_dir}\n")
        
        for sessao in sessoes:
            print(f"\n{'='*60}")
            print(f"📱 Sessão: {sessao.nome} (ID: {sessao.id})")
            print(f"   Status: {sessao.status}")
            print(f"   Telefone: {sessao.telefone or 'N/A'}")
            
            # Verificar arquivo de sessão
            db_path = f"{sessao_dir}/sessao_{sessao.id}.db"
            arquivo_existe = os.path.exists(db_path)
            print(f"   Arquivo: {'✅ Existe' if arquivo_existe else '❌ Não existe'}")
            
            # Se está desconectado ou com erro, limpar
            if sessao.status in ["desconectado", "erro"]:
                print(f"\n   🔧 Limpando sessão desconectada...")
                
                # Limpar QR Code do banco
                sessao.qr_code = None
                sessao.qr_code_gerado_em = None
                sessao.status = "desconectado"
                
                # Remover arquivo de sessão
                if arquivo_existe:
                    try:
                        os.remove(db_path)
                        print(f"   ✅ Arquivo removido: {db_path}")
                    except Exception as e:
                        print(f"   ❌ Erro ao remover arquivo: {e}")
                
                print(f"   ✅ Sessão limpa no banco de dados")
            elif sessao.status == "conectado":
                print(f"   ⚠️  Sessão marcada como conectada, mas pode estar desconectada.")
                print(f"   💡 Dica: Tente desconectar pela interface antes de limpar.")
        
        # Commit das alterações
        db.commit()
        
        print(f"\n{'='*60}")
        print("✅ Limpeza concluída!")
        print("\n💡 Próximos passos:")
        print("   1. Reinicie o servidor (Ctrl+C e rode novamente)")
        print("   2. Acesse a interface web")
        print("   3. Conecte novamente com QR Code")
        
    except Exception as e:
        print(f"❌ Erro durante limpeza: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def limpar_todas_sessoes():
    """Limpa TODAS as sessões (incluindo conectadas). Use com cuidado!"""
    print("⚠️  ATENÇÃO: Isso irá limpar TODAS as sessões, incluindo conectadas!")
    resposta = input("   Tem certeza? (sim/não): ").lower().strip()
    
    if resposta != "sim":
        print("❌ Operação cancelada.")
        return
    
    print("\n🧹 Limpando TODAS as sessões...\n")
    
    db = SessionLocal()
    
    try:
        # Obter diretório de sessões configurado
        sessao_dir = ConfiguracaoService.obter_valor(db, "sessao_diretorio", "./sessoes")
        
        sessoes = db.query(Sessao).all()
        
        for sessao in sessoes:
            print(f"🔧 Limpando sessão: {sessao.nome} (ID: {sessao.id})")
            
            # Limpar QR Code do banco
            sessao.qr_code = None
            sessao.qr_code_gerado_em = None
            sessao.status = "desconectado"
            
            # Remover arquivo de sessão
            db_path = f"{sessao_dir}/sessao_{sessao.id}.db"
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                    print(f"   ✅ Arquivo removido: {db_path}")
                except Exception as e:
                    print(f"   ❌ Erro ao remover arquivo: {e}")
        
        db.commit()
        print("\n✅ Todas as sessões foram limpas!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║          FLUXI - LIMPADOR DE SESSÕES WHATSAPP           ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    print("Escolha uma opção:")
    print("1. Limpar apenas sessões desconectadas (recomendado)")
    print("2. Limpar TODAS as sessões (use com cuidado!)")
    print("3. Sair")
    
    opcao = input("\nOpção: ").strip()
    
    if opcao == "1":
        limpar_sessoes()
    elif opcao == "2":
        limpar_todas_sessoes()
    else:
        print("❌ Saindo...")
