# ShopBot_Coding_Assesment_Sales_Genio_JMM
This is an evaluation of Flask powered API using a GPT-4o endpoint. This ShopBot is dedicated for providing information about customized (generated) Mock JSON catalogs.

First install the requirements in a previously loaded using this

```python
   pip install -r requirements.txt
```

Remember to first configure the API release installing the **postgresql** package.

```bash
apt install postgresql postgresql-*
```
Remember that this command will install the **postgresql** version associated to the latest (or currently installed) Linux distribution in your machine.

Subsequently, you must configure the database to do queries from the **fastAPI** session. Then, you need to modify the files on this absolute paths in Ubuntu:

- **/etc/postgresql/16/main/pg_hba.conf**
- **/etc/postgresql/16/main/postgresql.conf**

Take into account that this path will be different for another Linux distros, as well as for Mac and Windows. Search for the absolute locations of those files in your corresponding OS.

In the **pg_hba.conf** file you must change the line 118 and change the defaul method from **peer** to **md5**. 

![image](https://github.com/user-attachments/assets/d0a89b51-a783-4581-888d-efc558ff88ce)

And for the **postgresql.conf** you must change the line 60 - uncommenting the line and changing the word  **localhost** for a * (asterisc symbol). This will allow the databse to read any IP not only the localhost.

![image](https://github.com/user-attachments/assets/0029c50f-4ae6-4bdb-ab01-f940603ad1dc)

After you modify this files and the corresponding please restart the **postgresql** service

```bash
service postgresql restart
```

You can, then, create the database associated to the default user **postgres** and set the password for the posgresql database. For this, we must first go to the **psql** terminal using the following command

```bash
sudo -u postgres psql
```

Next, we must set the password, for this particular case, the password is **DataBase** but you can set your own password for convinience and parse it as an environment variable for security reasons. So you need to run the following command from the psql terminal.

```bash
ALTER USER postgres PASSWORD 'Password';
```

Now, from outside the psql terminal, and being on your root terminal you must create the database name associated to the **postgres** like this. For this particular case this database is called **Shopdb**.

```bash
createdb -U postgres Shopdb;
```
You can finish the postgresql configuration just restarting the service again. Then, you are ready to deploy the API from the local Python environment.

Now you must run the **app.py** code just invoking the Python command as follows

```bash
python app.py
```

For a general information about how to use the this API and the code, please check this explanatory videp [https://drive.google.com/file/d/13GNCuubAO7gFk7jnhEOUeOYYFv5kOylb/view?usp=sharing](https://drive.google.com/file/d/13GNCuubAO7gFk7jnhEOUeOYYFv5kOylb/view?usp=sharing).
