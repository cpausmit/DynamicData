DynamicDataNote
===============

Dynamic Data Note for T3

These are tex files to be used for a standard CMS document repository.
For reference, check this 

```
svn update utils
svn update -N notes
svn update notes/IN-14-XXX
eval `./notes/tdr runtime -sh` # for sh. use -csh for tcsh.
cd notes/IN-14-XXX/trunk
# put the files in the repo in this folder
tdr --style=in b IN-14-XXX
```
