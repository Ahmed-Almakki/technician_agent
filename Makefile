run:
	clear
	PYTHONPATH=. streamlit run app/tech_agent.py
agent:
	clear
	python3 -m src.agent.main

eval_agent:
	clear
	python3 -m eval.run_eval