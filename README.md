ckanext-odn-ic2pc-sync
-------

CKAN Extenstion for synchronization of catalog records from internal catalog to public (external) catalog

Features:
* Adds publishing table to DB
* Adds Publishing tab to dataset management ONLY IF the dataset is public
* Allows to add / remove / edit external catalogs to dataset 

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

TODO
-------

* last update in the external catalog table

Licenses
-------

Code of this extension is licensed under [GNU Affero General Public License, Version 3.0](http://www.gnu.org/licenses/agpl-3.0.html) (see LICENSE.txt)
