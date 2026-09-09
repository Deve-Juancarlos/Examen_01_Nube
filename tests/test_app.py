import pytest


class TestEliminarPersona:
    def test_elimina_y_retorna_true_cuando_existe(self, app_module, fake_db):
        fake_db["should_delete"] = True

        result = app_module.eliminar_persona(7)

        assert result is True
        assert fake_db["committed"] is True
        assert fake_db["closed"] is True
        assert "where id" in fake_db["executed_sql"].lower()
        assert fake_db["executed_params"] == (7,)

    def test_retorna_false_si_no_encuentra_registro(self, app_module, fake_db):
        fake_db["should_delete"] = False
        fake_db["committed"] = False

        result = app_module.eliminar_persona(999)

        assert result is False
        assert fake_db["committed"] is False
        assert fake_db["rollback_called"] is True
        assert fake_db["closed"] is True

    def test_cierra_conexion_y_rollback_si_hay_excepcion(self, app_module, fake_db):
        from unittest.mock import patch
        with patch("app.conectar_db", side_effect=RuntimeError("boom")):
            with pytest.raises(RuntimeError):
                app_module.eliminar_persona(1)

        assert fake_db["closed"] is True


_FakeConnMarker = None



class TestRutaEliminar:
    def test_post_eliminar_existente_redirige(self, client, fake_db):
        fake_db["should_delete"] = True

        resp = client.post("/eliminar/3", follow_redirects=False)

        assert resp.status_code == 302
        assert "/administrar" in resp.headers["Location"]

    def test_post_eliminar_inexistente_retorna_404(self, client, fake_db):
        fake_db["should_delete"] = False

        resp = client.post("/eliminar/42")

        assert resp.status_code == 404
        assert b"no encontrado" in resp.data

    def test_ruta_con_id_no_entero_retorna_404(self, client):
        resp = client.post("/eliminar/abc")

        assert resp.status_code == 404

    def test_ruta_con_caracteres_especiales_retorna_404(self, client):
        resp = client.post("/eliminar/12%20345")

        assert resp.status_code == 404


class TestCrearYObtener:
    def test_crear_persona_ejecuta_insert(self, app_module, fake_db):
        app_module.crear_persona("12345678", "Juan", "Perez", "Calle 1", "999111222")

        assert fake_db["inserted"] is True
        assert fake_db["committed"] is True
        assert "INSERT INTO personas" in fake_db["executed_sql"]

    def test_obtener_registros_retorna_lista(self, app_module, fake_db):
        fake_db["next_fetchall_result"] = [
            (1, "111", "Ana", "Lopez", "Dir", "111"),
            (2, "222", "Luis", "Diaz", "Dir2", "222"),
        ]

        result = app_module.obtener_registros()

        assert len(result) == 2
        assert fake_db["fetchall_calls"] == 1


_FakeConnMarker = None
