
rm ./erk/resources/resources.py

cd resources

python3 build_resources.py > resources.qrc

pyrcc5 -o resources.py resources.qrc
mv resources.py ../erk/resources/resources.py

rm resources.qrc

cd ..

