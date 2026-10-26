# Database Recovery Steps

0. Stop the pod to prevent crashing 
(*note: make sure that argocd autoscaling is also off if applicable)
```bash
kubectl scale deploy -n sensors sensor-dashboard-and-collection-sensor-postgres --replicas=0
# verify pod is gone
kubectl get pods -n sensors -w  
```

1. Check the backup
```bash 
kubectl apply -f backup-check.yaml 
kubectl exec -n sensors backup-check -- ls -lh /backup
kubectl exec -n sensors backup-check -- pg_restore --list /backup/sensors-20261021-000001.dump | head -30
```

2. Export the corrupted data (for later analysis or restore testing)
```bash
kubectl apply -f rescue.yaml
kubectl wait -n sensors --for=condition=Ready pod/pgdata-rescue --timeout=120s
kubectl exec -n sensors pgdata-rescue -- ls -la /pgvol /pgvol/pgdata
# check the pvc size
kubectl exec -n sensors pgdata-rescue -- du -sh /pgvol
df -h .          # get free space on your machine
# copy off the data
kubectl exec -n sensors pgdata-rescue -- tar cf - -C /pgvol . | gzip > pgdata-corrupt-20261026.tar.gz
ls -lh pgdata-corrupt-20261026.tar.gz
# optional local backup 
kubectl cp -n sensors backup-check:/backup/sensors-20261021-000001.dump ./sensors-20261021-000001.dump

# move corrupted data
kubectl exec -n sensors pgdata-rescue -- mv /pgvol/pgdata /pgvol/pgdata.corrupt
kubectl exec -n sensors pgdata-rescue -- ls -la /pgvol
kubectl delete pod -n sensors pgdata-rescue
```

3. Check volume capacity and health
```bash
kubectl exec -n sensors pgdata-rescue -- df -h /pgvol
kubectl exec -n sensors pgdata-rescue -- df -i /pgvol
kubectl exec -n sensors pgdata-rescue -- du -sh /pgvol/pgdata.corrupt/pg_wal
kubectl describe pvc -n sensors sensor-dashboard-and-collection-pg-pvc
kubectl get pod -n sensors pgdata-rescue -o wide
```

4. move the volume over
```bash
# 1. Find the volume's directory
kubectl get pv pvc-5f596576-f45a-4be4-b846-2858869b376a -o jsonpath='{.spec.hostPath.path}{"\n"}'

# 2. See what's there (use the path printed above)
sudo ls -la <that-path>

sudo mv <that-path>/pgdata <that-path>/pgdata.corrupt
sudo ls -la <that-path>
```