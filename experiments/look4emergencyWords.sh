#! /bin/bash

echo "Looking for emergency words in local CB1 files..."
grep -ir 'onbudsman' ./cb1data/
grep -ir 'court' ./cb1data/
grep -ir 'tribunal' ./cb1data/
grep -ir 'urgent' ./cb1data/
grep -ir 'emergency' ./cb1data/
grep -ir 'angry' ./cb1data/
grep -ir 'dissatisfied' ./cb1data/
grep -ir 'escalation' ./cb1data/
echo "Done."

exit 0
