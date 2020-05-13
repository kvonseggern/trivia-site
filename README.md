# trivia-site

### Instructions to get this up and running on an EC2 instance:

Update system and install necessary programs:

```
sudo apt-get update

sudo apt-get install python3-pip apache2 libapache2-mod-wsgi-py3
```

Clone the project to your `/home/ubuntu` directory:

```
git clone "https://github.com/kvonseggern/trivia-site.git"
```

Move into the `trivia-site` directory:

```
cd trivia-site
```

Install venv, create a virtual environment, activate it, and install requirements:

```
sudo apt-get install python3-venv

python3 -m venv env

source env/bin/activate

pip3 install -r requirements.txt 
```

Put the `000-default.conf` file in `/etc/apache2/sites-enabled` folder.

Add/change the following to `mysite/settings.py`:

```
sudo nano mysite/settings.py

STATIC_ROOT = os.path.join(BASE_DIR, "static/")
ALLOWED_HOSTS=['EC2_DNS_NAME']
```

Run the following commands to get the site ready:

```
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
```

Run the following commands to give Apache proper permissions:

```
chmod 664 db.sqlite3
sudo chown :www-data db.sqlite3
sudo chown :www-data ~/trivia-site
```

Restart the Apache server:

```
sudo service apache2 restart
```

Finally, don't forget about the secret key.

To set as an environment variable:

```
SECRET_KEY='...'
export SECRET_KEY
```

Then, make it persistent by adding it to `/etc/environment`.

Other than that, enjoy!