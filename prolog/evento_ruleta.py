import random
import string

# Función para tirar la ruleta y obtener un color basado en las probabilidades
def tirar_ruleta():
    return determinar_color(random.randint(1, 37))

# Función para determinar el color según el número aleatorio
def determinar_color(numero):
    if numero == 1:
        return "verde"  # El 1 corresponde al verde (0 en la ruleta europea)
    else:
        # Intercalamos los colores rojo y negro. El 1 está verde, luego alternan.
        # Los números pares (excluyendo el 1) serán rojos y los impares serán negros.
        if (numero % 2 == 0):
            return "rojo"  # Los números pares son rojos
        else:
            return "negro"  # Los números impares son negros
        
# Definir la función lambda para calcular la ganancia
ganancia = lambda A_i, A_total_color, A_total_ruleta: (A_i / A_total_color) * A_total_ruleta

# Definir los codigos de salas de apuesta
def generar_codigo_sala():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))