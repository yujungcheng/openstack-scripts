#!/bin/bash
# CEPH version: Jewel
# Estimate finish time by average of 10 results with 3 seconds interval. 
# Single line command

for i in {1..10}; do ceph pg stat -f json | python -c "import sys, json; data=json.load(sys.stdin); print(data['misplaced_objects']/data['recovering_objects_per_sec']/60)"; sleep 3; done | awk '{s+=$1} END {printf "%.0f", s/10}' | xargs -L1 -I {} sh -c "echo -n 'Finished at: '; date -d'+ {} minutes'"


