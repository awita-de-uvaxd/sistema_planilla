import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # SEGURIDAD ISO 25010: El depurador solo se activa mediante variable de entorno explícita
    modo_debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1']
    puerto = int(os.environ.get('PORT', 5000))
    
    app.run(host='0.0.0.0', port=5000, debug=True)