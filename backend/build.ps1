$ErrorActionPreference = "Stop"
# docker compose down -v --remove-orphans
# docker compose up --build -d
# Start-Sleep -Seconds 5
# urpm migrate
# urpm createsuperuser --email=admin@routemandu.com --username=admin
urpm shell -c "drut=CustomUser.objects.create(username='drut',email='drut@routemandu.com');drut.set_password('drut');drut.is_active=True;drut.save();dy=PublicTransitAgency(id='DRT',name='Drut Yatayat',color='#FFFFFF',owner=drut);dy.save()"
urpm shell -c "mngr=CustomUser.objects.create(username='mngr',email='mngr@routemandu.com');mngr.set_password('mngr');mngr.is_active=True;mngr.save();my=PublicTransitAgency(id='MNGR',name='Mahanagar Yatayat',color='#FF0000',owner=mngr);my.save()"
urpm shell -c "sja=CustomUser.objects.create(username='sja',email='sja@routemandu.com');sja.set_password('sja');sja.is_active=True;sja.save();sy=PublicTransitAgency(id='SJA',name='Sajha Yatayat',color='#00FF00',owner=sja);sy.save()"
urpm runserver