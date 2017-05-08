# Push and Pull Scripts

The push and pull scripts allow you to download subsets of the
`/shares/gcp` data to your local machine, work on them and generate
new data, and upload the result back to Sacagawea.

## Setting up a local directory

To prepare a local directory, run `./setup.sh DIR`, specifying a
directory to prepare for syncing as `DIR`.  After you have done this,
the `DIR` directory will hold the push and pull scripts, as well as an
empty `synced` file which labels that directory as ready to be synced.

## Pulling data from Sacagawea

To download data from Sacagawea, navigate to your synced directory and
type
```
./pull.sh SUBDIR
```
where `SUBDIR` is a subdirectory of `/shares/gcp`.  For example, to
download all mortality data, you could run `./pull.sh
estimation/mortality`.

## Pushing data to Sacagawea

To upload your data back to Sacagawea, first make sure that your
synced folders are the way you want them.  All of the files you have
changed and all of the new files in your synced folders will be
uploaded.  To find out what would get uploaded, first navigate to your
synced directory and run
```
./check.sh
```

This will simulate an upload, telling you what will be sent.  If that
all looks okay, then you can run
```
./push.sh
```
