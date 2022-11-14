import docker
import docker.models.images as images

client = docker.from_env()

data: images.RegistryData = client.images.get_registry_data("postgres:latestshahim")

print(str(data))
