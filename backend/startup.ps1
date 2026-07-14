$ErrorActionPreference = "Stop"
docker compose down -v --remove-orphans
docker compose up --build -d
Start-Sleep -Seconds 5
urpm migrate
urpm createsuperuser --email=admin@routemandu.com --username=admin
urpm shell -c "drut=CustomUser.objects.create(username='drut',email='drut@routemandu.com');drut.set_password('drut');drut.save();dy=PublicTransitAgency.objects.create(name='Drut Yatayat',color='#FFFFFF',owner=drut);dy.save()"