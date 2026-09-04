run:
	clear
	PYTHONPATH=. streamlit run src/app/tech_agent.py
agent:
	clear
	python3 -m src.agent.main