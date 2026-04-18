import asyncio
import random
import time
import json
from azure.iot.device.aio import IoTHubDeviceClient, ProvisioningDeviceClient
from azure.iot.device import Message

# --- CONFIGURACIÓN DE CREDENCIALES ---
ID_SCOPE = "0ne00F75E7B"
DEVICE_ID = "cargador-py-01" 
PRIMARY_KEY = "AR8MP0NIk4cvaoOkcNt7Urqyo0bTizMgvUC3aooMAOI="
PROVISIONING_HOST = "global.azure-devices-provisioning.net"

async def provision_device():
    provisioning_client = ProvisioningDeviceClient.create_from_symmetric_key(
        provisioning_host=PROVISIONING_HOST,
        registration_id=DEVICE_ID,
        id_scope=ID_SCOPE,
        symmetric_key=PRIMARY_KEY,
    )
    return await provisioning_client.register()

async def main():
    print(f"--- Iniciando Cargador Frontal: {DEVICE_ID} ---")
    
    # 1. Registro via DPS
    registration_result = await provision_device()
    if registration_result.status != "assigned":
        print("Error en el registro del dispositivo.")
        return

    # 2. Creación del cliente de telemetría
    client = IoTHubDeviceClient.create_from_symmetric_key(
        symmetric_key=PRIMARY_KEY,
        hostname=registration_result.registration_state.assigned_hub,
        device_id=DEVICE_ID,
    )

    await client.connect()
    print("Conexión establecida con éxito.")

    try:
        iteracion = 0
        while True:
            estado_actual = "ONLINE"

            # SIMULACIÓN DE DESCONEXIÓ
            if iteracion > 0 and iteracion % 12 == 0:
                print("\n[EVENTO] Señal débil detectada. Avisando a la nube y entrando en modo Offline...")
                
                # Reporte pre-desconexión
                msg_alerta = Message(json.dumps({"EstadoMaquina": "OFFLINE"}))
                msg_alerta.content_encoding = "utf-8"
                msg_alerta.content_type = "application/json"
                await client.send_message(msg_alerta)
                
                # Desconexión asíncrona
                await client.disconnect()
                await asyncio.sleep(15) 
                
                # Reconexión
                print("[EVENTO] Reestableciendo conexión asíncrona...")
                await client.connect()
                estado_actual = "ONLINE"

            
            t_motor = round(random.uniform(78.5, 102.0), 2)
            p_aceite = round(random.uniform(2.5, 4.8), 2)
            vibracion = round(random.uniform(5.0, 18.0), 2)

            
            payload = {
                "TemperaturaMotor": t_motor,
                "PresionAceite": p_aceite,
                "Vibracion": vibracion,
                "EstadoMaquina": estado_actual,
                "Ubicacion": {
                    "lat": 7.1297 + random.uniform(-0.001, 0.001),
                    "lon": -73.1258 + random.uniform(-0.001, 0.001)
                }
            }

            msg = Message(json.dumps(payload))
            msg.content_encoding = "utf-8"
            msg.content_type = "application/json"

            print(f"Enviando Telemetría [{iteracion}]: Estado {estado_actual} | Datos: {payload}")
            await client.send_message(msg)
            
            iteracion += 1
            await asyncio.sleep(8) # Frecuencia de envío

    except KeyboardInterrupt:
        print("Apagando motor del cargador...")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())