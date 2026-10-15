"""Optional Postgres checkpoints for hosts with an ephemeral filesystem."""
import threading


class PostgresPersistence:
    def __init__(self, url):
        import psycopg
        self.lock = threading.RLock()
        self.connection = psycopg.connect(url, autocommit=True, connect_timeout=10)
        # The executor and local workspace cache require exactly one application
        # process, including while a host replaces an old deployment.
        if not self.connection.execute('SELECT pg_try_advisory_lock(714932816)').fetchone()[0]:
            self.connection.close()
            raise RuntimeError('Another audit server is using this database. Stop it before starting this server.')
        self.connection.execute('CREATE TABLE IF NOT EXISTS audit_state (key text PRIMARY KEY, value bytea NOT NULL)')
        self.connection.execute('CREATE TABLE IF NOT EXISTS audit_runs (id text PRIMARY KEY, record bytea NOT NULL, archive bytea)')

    def get(self, key):
        with self.lock:
            row = self.connection.execute('SELECT value FROM audit_state WHERE key = %s', (key,)).fetchone()
            return bytes(row[0]) if row else None

    def put(self, key, value):
        with self.lock:
            self.connection.execute('INSERT INTO audit_state VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value', (key, value))

    def save_run(self, rid, record, archive=None):
        with self.lock:
            self.connection.execute('INSERT INTO audit_runs VALUES (%s, %s, %s) ON CONFLICT (id) DO UPDATE SET record = EXCLUDED.record, archive = COALESCE(EXCLUDED.archive, audit_runs.archive)', (rid, record, archive))

    def runs(self):
        with self.lock:
            return [(rid, bytes(record), bytes(archive) if archive is not None else None)
                    for rid, record, archive in self.connection.execute('SELECT id, record, archive FROM audit_runs').fetchall()]

    def close(self):
        with self.lock:
            self.connection.close()

    def ping(self):
        with self.lock:
            self.connection.execute('SELECT 1').fetchone()
