###################
#    Guilded.py
###################

develop:
	@echo ""
	@echo "--------------------------------------------------------------------"
	@echo "Installing development dependencies"
	@pip uninstall -y guilded.py || true
	@pip install -r requirements.txt
	@echo ""
	@echo "--------------------------------------------------------------------"
	@echo "Setting up development environment"
	@python setup.py develop
	@echo ""
	@echo "Done"
	@echo
