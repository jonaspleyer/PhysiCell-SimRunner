CC:=/usr/bin/python
OPTIONS:=
TESTDIR:=test
SAVEDIR:=save_dir

run:
	$(CC) $(OPTIONS) main.py

test_All:
	$(CC) -m unittest -v test.test_All

test_Parameter:
	$(CC) -m unittest -v test.test_Parameter

test_SimController:
	$(CC) -m unittest -v test.test_SimController

clean:
	rm -rf $(SAVEDIR)/run_*
