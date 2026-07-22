"""Clase pentru transmiterea obiectelor Python prin socketuri TCP.

Obiectele sunt transformate în bytes folosind pickle înainte de
transmitere și sunt reconstruite după ce au fost primite.
"""

import socket
import select
import pickle
import datetime

from typing import *


class ObjectSocketParams:
    """Conține parametrii utilizați la transmiterea obiectelor.

    Attributes:
        OBJECT_HEADER_SIZE_BYTES (int): Dimensiunea headerului care conține
            mărimea obiectului, exprimată în bytes.
        DEFAULT_TIMEOUT_S (int): Timpul implicit de așteptare, în secunde.
        CHUNK_SIZE_BYTES (int): Numărul maxim de bytes citiți simultan.
    """

    OBJECT_HEADER_SIZE_BYTES = 4
    DEFAULT_TIMEOUT_S = 1
    CHUNK_SIZE_BYTES = 1024


class ObjectSenderSocket:
    """Socket TCP folosit pentru trimiterea obiectelor Python."""

    ip: str
    port: int
    sock: socket.socket
    conn: socket.socket
    print_when_awaiting_receiver: bool
    print_when_sending_object: bool

    def __init__(
            self,
            ip: str,
            port: int,
            print_when_awaiting_receiver: bool = False,
            print_when_sending_object: bool = False):
        """Inițializează socketul care trimite obiecte.

        Args:
            ip (str): Adresa IP pe care socketul așteaptă conexiunea.
            port (int): Portul folosit pentru comunicare.
            print_when_awaiting_receiver (bool, optional): Dacă este True,
                afișează mesaje în timpul așteptării receiverului.
                Valoarea implicită este False.
            print_when_sending_object (bool, optional): Dacă este True,
                afișează informații despre obiectele trimise.
                Valoarea implicită este False.

        Returns:
            None: Constructorul nu returnează o valoare.
        """

        self.ip = ip
        self.port = port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.ip, self.port))
        self.conn = None

        self.print_when_awaiting_receiver = print_when_awaiting_receiver
        self.print_when_sending_object = print_when_sending_object

        self.await_receiver_conection()

    def await_receiver_conection(self):
        """Așteaptă conectarea unui receiver.

        Socketul începe să asculte și execuția este blocată până când
        un receiver se conectează.

        Returns:
            None: Metoda nu returnează o valoare.
        """

        if self.print_when_awaiting_receiver:
            print(
                f'[{datetime.datetime.now()}]'
                f'[ObjectSenderSocket/{self.ip}:{self.port}] '
                f'awaiting receiver connection...'
            )

        self.sock.listen(1)
        self.conn, _ = self.sock.accept()

        if self.print_when_awaiting_receiver:
            print(
                f'[{datetime.datetime.now()}]'
                f'[ObjectSenderSocket/{self.ip}:{self.port}] '
                f'receiver connected'
            )

    def close(self):
        """Închide conexiunea curentă cu receiverul.

        După închidere, atributul conn este setat la None.

        Returns:
            None: Metoda nu returnează o valoare.
        """

        self.conn.close()
        self.conn = None

    def is_connected(self) -> bool:
        """Verifică dacă există o conexiune cu receiverul.

        Returns:
            bool: True dacă atributul conn nu este None, altfel False.
        """

        return self.conn is not None

    def send_object(self, obj: Any):
        """Trimite un obiect Python către receiver.

        Obiectul este serializat cu pickle. Mai întâi este trimisă
        dimensiunea obiectului, apoi obiectul propriu-zis.

        Args:
            obj (Any): Obiectul Python care trebuie trimis. Acesta trebuie
                să poată fi serializat folosind pickle.

        Returns:
            None: Metoda nu returnează o valoare.
        """

        data = pickle.dumps(obj)
        data_size = len(data)

        data_size_encoded = data_size.to_bytes(
            ObjectSocketParams.OBJECT_HEADER_SIZE_BYTES,
            'little'
        )

        self.conn.sendall(data_size_encoded)
        self.conn.sendall(data)

        if self.print_when_sending_object:
            print(
                f'[{datetime.datetime.now()}]'
                f'[ObjectSenderSocket/{self.ip}:{self.port}] '
                f'Sent object of size {data_size} bytes.'
            )


class ObjectReceiverSocket:
    """Socket TCP folosit pentru primirea obiectelor Python."""

    ip: str
    port: int
    conn: socket.socket
    print_when_connecting_to_sender: bool
    print_when_receiving_object: bool

    def __init__(
            self,
            ip: str,
            port: int,
            print_when_connecting_to_sender: bool = False,
            print_when_receiving_object: bool = False):
        """Inițializează socketul care primește obiecte.

        Args:
            ip (str): Adresa IP a senderului.
            port (int): Portul pe care senderul așteaptă conexiunea.
            print_when_connecting_to_sender (bool, optional): Dacă este True,
                afișează mesaje în timpul conectării. Valoarea implicită
                este False.
            print_when_receiving_object (bool, optional): Dacă este True,
                afișează informații despre obiectele primite. Valoarea
                implicită este False.

        Returns:
            None: Constructorul nu returnează o valoare.
        """

        self.ip = ip
        self.port = port
        self.print_when_connecting_to_sender = (
            print_when_connecting_to_sender
        )
        self.print_when_receiving_object = print_when_receiving_object

        self.connect_to_sender()

    def connect_to_sender(self):
        """Creează socketul TCP și se conectează la sender.

        Este folosită adresa IP și portul primite în constructor.

        Returns:
            None: Metoda nu returnează o valoare.
        """

        if self.print_when_connecting_to_sender:
            print(
                f'[{datetime.datetime.now()}]'
                f'[ObjectReceiverSocket/{self.ip}:{self.port}] '
                f'connecting to sender...'
            )

        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.ip, self.port))

        if self.print_when_connecting_to_sender:
            print(
                f'[{datetime.datetime.now()}]'
                f'[ObjectReceiverSocket/{self.ip}:{self.port}] '
                f'connected to sender'
            )

    def close(self):
        """Închide conexiunea curentă cu senderul.

        După închidere, atributul conn este setat la None.

        Returns:
            None: Metoda nu returnează o valoare.
        """

        self.conn.close()
        self.conn = None

    def is_connected(self) -> bool:
        """Verifică dacă există o conexiune cu senderul.

        Returns:
            bool: True dacă atributul conn nu este None, altfel False.
        """

        return self.conn is not None

    def recv_object(self) -> Any:
        """Primește și reconstruiește un obiect Python.

        Mai întâi este citită dimensiunea obiectului, apoi sunt citite
        toate datele. Obiectul este reconstruit folosind pickle.loads().

        Returns:
            Any: Obiectul Python primit de la sender.
        """

        obj_size_bytes = self._recv_object_size()
        data = self._recv_all(obj_size_bytes)
        obj = pickle.loads(data)

        if self.print_when_receiving_object:
            print(
                f'[{datetime.datetime.now()}]'
                f'[ObjectReceiverSocket/{self.ip}:{self.port}] '
                f'Received object of size {obj_size_bytes} bytes.'
            )

        return obj

    def _recv_with_timeout(
            self,
            n_bytes: int,
            timeout_s: float =
            ObjectSocketParams.DEFAULT_TIMEOUT_S) -> Optional[bytes]:
        """Încearcă să primească date într-un anumit interval de timp.

        Args:
            n_bytes (int): Numărul maxim de bytes care trebuie citiți.
            timeout_s (float, optional): Timpul maxim de așteptare,
                exprimat în secunde. Valoarea implicită este
                ObjectSocketParams.DEFAULT_TIMEOUT_S, adică o secundă.

        Returns:
            Optional[bytes]: Datele primite sau None dacă timpul de
            așteptare a expirat.
        """

        rlist, _1, _2 = select.select(
            [self.conn],
            [],
            [],
            timeout_s
        )

        if rlist:
            data = self.conn.recv(n_bytes)
            return data
        else:
            return None

    def _recv_all(
            self,
            n_bytes: int,
            timeout_s: float =
            ObjectSocketParams.DEFAULT_TIMEOUT_S) -> bytes:
        """Primește exact numărul de bytes specificat.

        Datele sunt citite în bucăți de maximum CHUNK_SIZE_BYTES.

        Args:
            n_bytes (int): Numărul total de bytes care trebuie primiți.
            timeout_s (float, optional): Timpul maxim de așteptare pentru
                fiecare bucată de date. Valoarea implicită este o secundă.

        Returns:
            bytes: Toate datele primite, reunite într-un singur obiect bytes.

        Raises:
            socket.error: Dacă timpul de așteptare expiră înainte ca toate
                datele să fie primite.
        """

        data = []
        left_to_recv = n_bytes

        while left_to_recv > 0:
            desired_chunk_size = min(
                ObjectSocketParams.CHUNK_SIZE_BYTES,
                left_to_recv
            )

            chunk = self._recv_with_timeout(
                desired_chunk_size,
                timeout_s
            )

            if chunk is not None:
                data += [chunk]
                left_to_recv -= len(chunk)
            else:
                bytes_received = sum(map(len, data))

                raise socket.error(
                    'Timeout elapsed without any new data being received. '
                    f'{bytes_received} / {n_bytes} bytes received.'
                )

        data = b''.join(data)
        return data

    def _recv_object_size(self) -> int:
        """Primește dimensiunea următorului obiect.

        Citește headerul de 4 bytes și îl transformă într-un număr întreg
        folosind ordinea little-endian.

        Returns:
            int: Dimensiunea în bytes a obiectului care urmează să fie primit.
        """

        data = self._recv_all(
            ObjectSocketParams.OBJECT_HEADER_SIZE_BYTES
        )

        obj_size_bytes = int.from_bytes(data, 'little')
        return obj_size_bytes