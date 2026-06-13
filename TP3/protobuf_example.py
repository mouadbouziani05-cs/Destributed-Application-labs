import user_pb2

user = user_pb2.User()
user.id = 1
user.name = "Ali"

binary_data = user.SerializeToString()

print("Données binaires :", binary_data)

new_user = user_pb2.User()
new_user.ParseFromString(binary_data)

print("Utilisateur :", new_user)
