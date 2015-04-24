ckanext-odn-ic2pc-sync
-------

CKAN Extenstion for synchronization of catalog records from internal catalog to public (external) catalog

Features:
* Adds publishing table to DB
* Adds Publishing tab to dataset management ONLY IF the dataset is public
* Allows to add / remove / edit external catalogs to dataset
* Starts synchronization with default (from .ini file) and external catalogs whenever package is created/updated or package resource was created / updated / deleted
* Allows to start the synchronization to public or external catalogs manually from publishing tab
* Added new API calls: datastore_primary_key, datastore_indexes
* Added datastore resource synchronization, but can't be used as harvesting for datastore resources because of the new datastore API calls 

Installation
-------


(Optional): activate ckan virtualenv ``` . /usr/lib/ckan/default/bin/activate ```

From the extension folder start the installation: ``` python setup.py install ```

Add extension to ckan config: /etc/ckan/default/production.ini

```ApacheConf
[app:main]
# for starting sync job through command line only
odn.ic2pc.src.ckan.url = http://localhost
odn.ic2pc.dst.ckan.url = http://destination_ckan.com
odn.ic2pc.dst.ckan.api.key = c2ca3375-6d0e-44ec-927f-c380e4cf06df

# used by command line and plugin too, blank space as delimiter
odn.ic2pc.package.extras.whitelist = creator dataset license modified publisher void#sparqlEndpoint
odn.ic2pc.resource.extras.whitelist = license

ckan.plugins = odn_ic2pc_sync
```

DB init
-------

After installing plugin and restarting apache server start db initialization:

```
paster --plugin=ckanext-odn-ic2pc-sync odn_ic2pc_sync_cmd initdb --config=/etc/ckan/default/production.ini
```

There should be output like this:
```
Starting db initialization
creating external_catalog table				/ Or if it was already intialized:
external_catalog table created successfully	/ external_catalog table already exists
End of db initialization
```

Migrating DB from v0.2.x to v0.3.0
-------
There were changes in DB model with migrating to v0.3.0, to function normally, its required to start this command

```
paster --plugin=ckanext-odn-ic2pc-sync odn_ic2pc_sync_cmd migrate_to_v0.3.0 --config=/etc/ckan/default/production.ini
```

If its clean install, starting the migration command isn't necessary.

Migrating DB from v0.3.x to v0.4.0
-------

```
paster --plugin=ckanext-odn-ic2pc-sync odn_ic2pc_sync_cmd migrate_to_v0.4.0 --config=/etc/ckan/default/production.ini
```

Uninstall
-------

Before removing extension start:

```
paster --plugin=ckanext-odn-ic2pc-sync odn_ic2pc_sync_cmd uninstall --config=/etc/ckan/default/production.ini
```

This will drop tables created in DB init script.

Now you can remove plugin string from: ``` /etc/ckan/default/production.ini ```

Restart apache server: ``` sudo service apache2 restart ```

And remove from python installed extension egg.

Running the sync job
-------
```
paster --plugin=ckanext-odn-ic2pc-sync odn_ic2pc_sync_cmd run --config=/etc/ckan/default/production.ini
```

example:
````
paster --plugin=ckanext-odn-ic2pc-sync odn_ic2pc_sync_cmd test --config=/etc/ckan/default/production.ini
```

should have output like this:
```
test command started
source ckan url:      http://localhost
destination ckan url: http://destination_ckan.com
destination api key:  c2ca3375-6d0e-44ec-927f-c380e4cf06df
package extras whitelist:  creator dataset license modified publisher void#sparqlEndpoint
resource extras whitelist: license
```

Creating cron job
-------

Edit cron table to create a cron job, that will run dataset pusher command periodically
````
sudo crontab -e -u user_name
```

example:
```
# m  h  dom mon dow   command
*/15 *  *   *   *     /usr/bin/paster --plugin=ckanext-odn-ic2pc-sync odn_ic2pc_sync_cmd run --config=/etc/ckan/default/production.ini
```

this example will check for pending jobs every fifteen minutes

Internationalization (i18n)
-------
CKAN supports internationalization through babel (```pip install babel```). This tool extracts the messages from source code and html files
and creates .pot file. Next using commands (step 2 or 3) it creates or updates .po files. The actual translation are in these .po files.

1. To extract new .pot file from sources
	```
	python setup.py extract_messages
	```
	
	This need to be done if there is no .pot file or there were some changes to messages in source code files or html files.

2. To generate .po for new localization (this example uses 'sk' localization)
	```
	python setup.py init_catalog --locale sk
	```

3. If only updating existing .po file (e.g. new messages were extracted through step 1)
	```
	python setup.py update_catalog --locale sk
	```

Licenses
-------

Code of this extension is licensed under [GNU Affero General Public License, Version 3.0](http://www.gnu.org/licenses/agpl-3.0.html) (see LICENSE.txt)
