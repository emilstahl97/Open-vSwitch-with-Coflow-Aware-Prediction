class BaseIPv4Generator:
    
    def __init__(self, excluded_subnets=[]):

        self.excluded_first_octets = set()
        for subnet in excluded_subnets:
            subnet_parts = subnet.split('.')
            if len(subnet_parts) >= 1:
                self.excluded_first_octets.add(subnet_parts[0])

    def add_excluded_subnet(self, subnet: str):
        subnet_parts = subnet.split('.')
        if len(subnet_parts) >= 1:
            self.excluded_first_octets.add(subnet_parts[0])
    

    def get_unique_base_src_ip(self, x) -> str:
        # Check if x is within the valid range
        if x < 0:
            raise ValueError("Value of x must be greater than or equal to 0.")

        # Determine the first octet based on x and excluded subnets
        first_octet = '1'
        if x > 254 and len(self.excluded_first_octets) < 254:
            possible_first_octets = set(str(i) for i in range(1, 256)) - self.excluded_first_octets
            if possible_first_octets:
                first_octet = min(possible_first_octets)

        # Generate the IPv4 address
        if x <= 254:
            if first_octet in self.excluded_first_octets:
                # Find the next available first octet
                first_octet = min(set(str(i) for i in range(1, 256)) - self.excluded_first_octets)
            return f'{first_octet}.1.0.{x}'
        else:
            third_octet = (x - 255) // 256 + 1
            fourth_octet = (x - 255) % 256
            return f'{first_octet}.1.{third_octet}.{fourth_octet}'
        

if __name__ == "__main__":

    # Initialize the IPv4Generator object with excluded subnets
    excluded_subnets = ['1.0.0.0', '2.0.0.0', '3.0.0.0', '40.0.0.0', '4.255.255.254']
    ipv4_generator = BaseIPv4Generator(excluded_subnets)

    # Test the generate_ipv4_address method

    unique_ipv4_addresses = set()

    for x in range(20000):
        ipv4_address = ipv4_generator.generate_src_ipv4_address(x)
        unique_ipv4_addresses.add(ipv4_address)
        print(f"Generated IPv4 address: {ipv4_address}")

    print(f"Number of unique IPv4 addresses generated: {len(unique_ipv4_addresses)}")
