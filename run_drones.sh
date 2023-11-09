#!/bin/bash

# Ejecuta 10 instancias de AD_Drone con diferentes IDs
for i in {1..10}
do
  python3 AD_Drone --Id $i &
done

# Espera a que todas las instancias finalicen
wait