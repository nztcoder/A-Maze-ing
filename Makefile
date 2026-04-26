install:
	python3 -m venv virt_env
	virt_env/bin/python3 -m pip install -r requirements.txt

run:
	virt_env/bin/python3 a_maze_ing.py config.txt

debug:
	virt_env/bin/python3 -m pdb -m a_maze_ing config.txt

clean:
	rm -rf __pycache__/
	rm -rf .mypy_cache/
	rm -rf virt_env/
	rm -rf mazegen/__pycache__/
# https://earthly.dev/blog/python-makefile/

lint:
	flake8 . & mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports \
	--disallow-untyped-defs --check-untyped-defs
