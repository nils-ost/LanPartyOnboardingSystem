# Setup Dev-Environment

```
virtualenv -p /usr/bin/python3 venv
venv/bin/pip install -r requirements.txt
cd frontend
npm install
cd node_modules/@angular/cli/bin
ln -s ng.js ng
cd ../../../../..
echo -e "source venv/bin/activate\nunset PS1\nPATH_add frontend/node_modules/@angular/cli/bin" > .envrc
direnv allow
```