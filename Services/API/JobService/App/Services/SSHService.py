import paramiko
import os
from decouple import config
from fastapi import HTTPException


class SSHService:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.sftp = None

    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.host, port=self.port, username=self.username, password=self.password)
            self.sftp = self.client.open_sftp()
            print("SSH connection established.")
        except Exception as e:
            print(f"Error establishing SSH connection: {e}")
            raise HTTPException(status_code=500, detail="SSH connection failed.")

    def upload_file(self, local_path: str, remote_path: str):
        try:

            if not os.path.exists(local_path):
                raise Exception(f"Local file {local_path} does not exist.")

            try:

                self.sftp.put(local_path, remote_path)
                print(f"File {local_path} uploaded to {remote_path}")

                chmod_command = f"chmod +x {remote_path}"
                stdin, stdout, stderr = self.client.exec_command(chmod_command)

                errors = stderr.read().decode('utf-8')
                if errors:
                    print(f"Error running chmod on {remote_path}: {errors}")
                else:
                    print(f"Successfully set executable permission on {remote_path}")

            except Exception as e:
                raise Exception(f"Error uploading file to remote path {remote_path}: {str(e)}")

        except Exception as e:
            print(f"Error in upload_file: {e}")
            raise e

    def download_file(self, remote_path: str, local_path: str):
        try:

            try:
                self.sftp.stat(remote_path)
            except FileNotFoundError:
                raise Exception(f"Remote file {remote_path} does not exist.")

            self.sftp.get(remote_path, local_path)
            print(f"File {remote_path} downloaded to {local_path}")

        except Exception as e:
            print(f"Error in download_file: {e}")
            raise e

    def execute_command(self, command: str, remote_path: str):
        try:

            chmod_command = f"chmod +x {remote_path}"
            stdin, stdout, stderr = self.client.exec_command(chmod_command)

            stdin, stdout, stderr = self.client.exec_command(command)

            command_output = stdout.read().decode('utf-8')
            command_error = stderr.read().decode('utf-8')

            print(f"Command output: {command_output}")
            print(f"Command error: {command_error}")

            if command_error:
                raise Exception(f"Error executing command: {command_error}")

            print(f"Command executed successfully: {command}")
            return command_output

        except Exception as e:
            print(f"Error executing command: {e}")
            raise HTTPException(status_code=500, detail=f"Error executing command: {str(e)}")

    def delete_file(self, remote_path: str):
        try:

            try:
                self.sftp.stat(remote_path)
            except FileNotFoundError:
                raise Exception(f"Remote file {remote_path} does not exist.")

            self.sftp.remove(remote_path)
            print(f"File {remote_path} deleted successfully.")

        except Exception as e:
            print(f"Error in delete_file: {e}")
            raise e

    def close(self):
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()
        print("SSH connection closed.")
