import asyncio
from bleak import BleakClient

# UUIDs for the BLE service and characteristic
SERVICE_UUID = "00001101-0000-1000-8000-00805F9B34FB" 
CHARACTERISTIC_UUID = "00002101-0000-1000-8000-00805F9B34FB"  

async def main(address):
    """
    Main function to connect to the BLE server (Flutter app) and process commands.
    
    Args:
        address (str): The MAC address or UUID of the BLE server (Flutter app).
    """
    try:
        async with BleakClient(address) as client:
            print(f"Connected to BLE server at {address}")

            # Continuously read data from the characteristic
            while True:
                try:
                    # Read the characteristic value
                    data = await client.read_gatt_char(CHARACTERISTIC_UUID)
                    command = data.decode()
                    print(f"Received data: {command}")

                    # Send a response back to the server
                    response = "Message received!".encode()
                    await client.write_gatt_char(CHARACTERISTIC_UUID, response)

                except Exception as e:
                    print(f"Error during BLE communication: {e}")
                    break

                # Wait before reading again
                await asyncio.sleep(1)

    except Exception as e:
        print(f"Failed to connect to BLE server: {e}")

if __name__ == "__main__":
    # Replace this with the MAC address or UUID of your Flutter app's BLE server
    BLE_SERVER_ADDRESS = "XX:XX:XX:XX:XX:XX" 

    # Run the BLE client
    asyncio.run(main(BLE_SERVER_ADDRESS))