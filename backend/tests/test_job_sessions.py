from app.api import auth, jobs
from app.main import app
from app.models import Tender


def test_jobs_require_cookie_even_in_public_demo(client, db, monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('PUBLIC_JUDGE_DEMO', 'true')
    client.cookies.clear()
    assert client.post('/api/jobs/tender/999').status_code == 401
    assert client.get('/api/jobs/unknown').status_code == 401


def test_authenticated_job_creation_polling_and_refresh(client, db, monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('PUBLIC_JUDGE_DEMO', 'true')
    app.dependency_overrides.pop(auth.require_processing)

    class Provider:
        def health(self):
            pass
        def metadata(self):
            return {'mode': 'ONLINE', 'provider': 'Groq', 'model': 'test'}

    monkeypatch.setattr(auth, 'get_provider', lambda mode: Provider())
    def finish(job_id, ai):
        job = db.get(jobs.ProcessingJob, job_id)
        job.status = 'COMPLETED'
        job.result = {'requirements': []}
        db.commit()
    monkeypatch.setattr(jobs, 'run_job', finish)
    tender = Tender(title='Session regression', external_bid_id='SESSION-TEST')
    db.add(tender)
    db.commit()
    response = client.post(f'/api/jobs/tender/{tender.id}')
    assert response.status_code == 202
    job_id = response.json()['job_id']
    assert client.get(f'/api/jobs/{job_id}').json()['status'] == 'COMPLETED'
    assert client.get('/api/auth/session').status_code == 200
    assert client.get('/api/auth/session').status_code == 200
    client.cookies.clear()
    assert client.get(f'/api/jobs/{job_id}').status_code == 401
