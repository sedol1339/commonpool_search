A set of tools for text search over CommonPool (aka DataComp) dataset.

Overall pipeline:
1. Clone repo and install requirements
2. Download CommonPool .parquet files (up to 3 TB)
3. Set up Solr search engine
4. Index files with Solr
5. Run server and open search.html file to search

# Install requirements

```
git clone git@github.com:sedol1339/commonpool_search.git
cd commonpool_search
python3.8 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

# Downloading CommonPool .parquet files

```
download_commonpool.py
```

| Argument | Description | Possible values | Default value |
|---|---|---|---|
| --subset | CommonPool subset to download. | small, medium, large, xlarge | xlarge |
| --folder | Folder to download. | any path | (equals subset name) |
| --part | Optional. If downloading xlarge subset, set this to download only a part of the subset. Part can be from 0 to 7. Value -1 means downloading all parts (3 TB). | -1, 0, ..., 7 | -1 |

After downloading, files will be placed into {folder}/hf_cache subfolder, and relative symlinks to parquet files will be created in {folder}. If you downloaded xlarge subset, symlinks are placed in subfolders {folder}/part_{i}. Then you need to move them to the {folder} after finishing donwnloading:

```
for dir in xlarge/part_*/; do
	for file in $dir*; do
		echo $file
		ln -s $(readlink -f $file) xlarge/${file##*/}
	done
done

rm -r xlarge/part_*
```

NOTE: if you remove .parquet symlinks from {folder}, you can run download_commonpool.py again - this will create symlinks to hf_cache again without re-downloading the files.

# Setting up Solr search engine and importing .csv files

Let your linux username is `linuxuser`, then run the following commands:

```
cd ~
wget https://www.apache.org/dyn/closer.lua/solr/solr/9.3.0/solr-9.3.0.tgz?action=download -O solr-9.3.0.tgz
tar xzf solr-9.3.0.tgz solr-9.3.0/bin/install_solr_service.sh --strip-components=2
sudo bash ./install_solr_service.sh solr-9.3.0.tgz -u linuxuser
```

By default, the script extracts the distribution archive into /opt, configures Solr to write files into /var/solr, and runs Solr as service. If you do not want to start the service immediately, pass the -n option to install script.

The following instruction will allow access to Solr from web. This is a security risk, so better to run this in the internal network.

Firstly, we allow allow cross-origin JS requests. In file `/opt/solr/server/solr-webapp/webapp/WEB-INF/web.xml`, add the following lines as the first child of <web-app> tag:

```
 <filter>
   <filter-name>cross-origin</filter-name>
   <filter-class>org.eclipse.jetty.servlets.CrossOriginFilter</filter-class>
   <init-param>
     <param-name>allowedOrigins</param-name>
     <param-value>*</param-value>
   </init-param>
   <init-param>
     <param-name>allowedMethods</param-name>
     <param-value>GET,POST,OPTIONS,DELETE,PUT,HEAD</param-value>
   </init-param>
   <init-param>
     <param-name>allowedHeaders</param-name>
     <param-value>origin, content-type, accept</param-value>
   </init-param>
 </filter>
 <filter-mapping>
   <filter-name>cross-origin</filter-name>
   <url-pattern>/*</url-pattern>
 </filter-mapping>
```

Then restart the service:

```
sudo service solr restart
```

Append the following lines in the end of the file `/etc/default/solr.in.sh`:

```
SOLR_JETTY_HOST="0.0.0.0"
SOLR_JAVA_MEM="-Xms2g -Xmx2g"
```

(change -Xms -Xmx to the desired maximum memory allocation pool for a Java Virtual Machine)

Move to the `commonpool_search` folder, then run the following command to Move `xmls` folder contents to Solr data folder.

```
cp xmls/* /var/solr/data/ -r
```

Create `commonpool` Solr core:

```
curl "http://localhost:8983/solr/admin/cores?action=CREATE&name=commonpool"
```

Just to check, the following request should return a json with "response" and "responseHeader" fields:

```
curl "http://localhost:8983/solr/commonpool/select?defType=edismax&df=Text&q=badger&start=0&rows=10"
```

# Index files with Solr

NOTE: this will require a long time.

Run the following script:

```
python index_commonpool_to_solr.py --folder xlarge --min_width 500 --min_height 500 \
 --solr_core commonpool --remove_parquet_on_success --shard_size 1
```

Argument of the `index_commonpool_to_solr.py` script:

| Argument | Description | Possible values | Default value |
|---|---|---|---|
| --folder | Folder with .parquet files. | any path | xlarge |
| --remove_parquet_on_success | Whether to remove .parquet files on successful indexing. | true | not specified (=false) |
| --min_width | Skip images with width lower than specified. | any integer | 0 |
| --min_height | Skip images with height lower than specified. | any integer | 0 |
| --solr_path | Path to Solr folder, from which bin/post file will be run. | any path | /opt/solr |
| --solr_core | Name of the Solr core. | any string | commonpool |
| --shard_size | One post request per {shard_size} .parquet files. Warning: high values may crash Solr. | any positive integer | 1 |

At any time, to make POSTed files searchable make COMMIT with the following request:

```
curl http://localhost:8983/solr/commonpool/update?commit=true
```

# Run server and open search.html file to search

Run the server:

```
cd commonpool_search
screen -S webserver
python -m http.server 8080
```

Then press Ctrl-A, Ctrl-D to detach from screen.

Then connect to your server, port 8080, open `search.html` and do a search. Solr request URLs will appear in the development console in your browser.

# Searching for required objects in other datasets

In folder `inspector`, you can find scripts for text-searching for any object in several existing datasets.