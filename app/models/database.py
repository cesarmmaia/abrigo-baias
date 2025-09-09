import sqlite3
import os
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'database.db')
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de desinfecções
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS baias_desinfeccao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_baia INTEGER NOT NULL,
                data_desinfeccao DATE,
                data_agendamento DATE,  -- NOVO: Data do agendamento
                metodo TEXT NOT NULL,
                observacao TEXT,
                status_agendamento TEXT DEFAULT 'pendente',  -- NOVO: pendente, realizado, cancelado
                criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # NOVA: Tabela de configurações de agendamento
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config_agendamento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intervalo_dias INTEGER DEFAULT 15,
                horario_padrao TIME DEFAULT '09:00:00',
                notificar_antes INTEGER DEFAULT 2,
                criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Inserir configuração padrão se não existir
        cursor.execute('SELECT COUNT(*) FROM config_agendamento')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO config_agendamento (intervalo_dias, horario_padrao, notificar_antes)
                VALUES (15, '09:00:00', 2)
            ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    # Métodos existentes mantidos...

    def get_all_desinfeccoes(self):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM baias_desinfeccao ORDER BY data_desinfeccao DESC')
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append(dict(row))

        conn.close()
        return result

    def insert_desinfeccao(self, numero_baia, data_desinfeccao, metodo, observacao):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO baias_desinfeccao (numero_baia, data_desinfeccao, metodo, observacao)
            VALUES (?, ?, ?, ?)
        ''', (numero_baia, data_desinfeccao, metodo, observacao))

        conn.commit()
        last_id = cursor.lastrowid
        conn.close()

        return last_id

    def update_desinfeccao(self, id, numero_baia, data_desinfeccao, metodo, observacao):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE baias_desinfeccao 
            SET numero_baia = ?, data_desinfeccao = ?, metodo = ?, observacao = ?, atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (numero_baia, data_desinfeccao, metodo, observacao, id))

        conn.commit()
        conn.close()

    def delete_desinfeccao(self, id):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM baias_desinfeccao WHERE id = ?', (id,))

        conn.commit()
        conn.close()
  
    
    # NOVOS MÉTODOS PARA AGENDAMENTO
    def get_proximo_agendamento(self, numero_baia):
        """Retorna a data do próximo agendamento para uma baia"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT MAX(data_desinfeccao) as ultima_desinfeccao 
            FROM baias_desinfeccao 
            WHERE numero_baia = ? AND status_agendamento = 'realizado'
        ''', (numero_baia,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result['ultima_desinfeccao']:
            ultima_data = datetime.strptime(result['ultima_desinfeccao'], '%Y-%m-%d')
            intervalo = self.get_intervalo_agendamento()
            return ultima_data + timedelta(days=intervalo)
        return None
    
    def get_intervalo_agendamento(self):
        """Retorna o intervalo padrão entre desinfecções"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT intervalo_dias FROM config_agendamento LIMIT 1')
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 15
    
    def get_agendamentos_pendentes(self):
        """Retorna todos os agendamentos pendentes"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM baias_desinfeccao 
            WHERE status_agendamento = 'pendente' 
            ORDER BY data_agendamento ASC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def criar_agendamento(self, numero_baia, data_agendamento, metodo, observacao=''):
        """Cria um novo agendamento"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO baias_desinfeccao (numero_baia, data_desinfeccao, data_agendamento, metodo, observacao, status_agendamento)
            VALUES (?, NULL, ?, ?, ?, 'pendente')
        ''', (numero_baia, data_agendamento, metodo, observacao))
        
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        
        return last_id
    
    def realizar_agendamento(self, id_agendamento, data_realizacao): #Tirei o = None
        """Marca um agendamento como realizado"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        data_real = data_realizacao or datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            UPDATE baias_desinfeccao 
            SET data_desinfeccao = ?, status_agendamento = 'realizado', atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (data_real, id_agendamento))
        
        conn.commit()
        conn.close()

def update_config_agendamento(self, intervalo_dias):
    conn = self.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE config_agendamento SET intervalo_dias = ?, criado_em = CURRENT_TIMESTAMP WHERE id = 1', 
                   (intervalo_dias,))
    
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated