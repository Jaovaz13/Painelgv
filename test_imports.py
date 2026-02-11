try:
    print("Testing imports...")
    import config
    print("Config imported")
    import database
    print("Database imported")
    from analytics.estimativa_pib import estimar_pib
    print("Analytics imported")
    from panel.painel import main
    print("Panel imported")
    print("SUCCESS: All imports working.")
except Exception as e:
    import traceback
    traceback.print_exc()
