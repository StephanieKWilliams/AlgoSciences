The project is written with python --version 3.6.15

You can set up a virtual environment (optional)
    -pip install virtualenv
    -python -m venv venv
    -source venv/bin/activate





1.Steps to Set Everything Up:

    Place the Python Script (script.py) at a desired location (e.g., /home/user/my_daemon/script.py).

2.Install the requirements
    pip install -r requirements.txt


3.Create the Configuration File (config.ini) in /etc/algosciences/config.ini.
    have items that are in the projects config.ini here
            

4.Create the systemd Service File (algoscience.service) in /etc/systemd/system/.
    create the service file 



        [Unit]
        Description=Algosciences
        After=network.target

        [Service]
        ExecStart=/usr/bin/python3 /path/to/your/client.py
        WorkingDirectory=/path/to/your
        StandardOutput=file:/var/log/algoscience.log
        StandardError=file:/var/log/algoscience.log
        User=your_user
        Group=your_group
        Restart=on-failure

        [Install]
        WantedBy=multi-user.target

5.Reload the systemd daemon:

    sudo systemctl daemon-reload

6.Enable the service to start on boot:

    sudo systemctl enable algoscience.service

7.Start the service:

    sudo systemctl start algoscience.service

Now, your Python script should run as a service (daemon) managed by systemd.

Open your browser on the specified ip address and port number

sudo tail /var/log/algosciences.log
  -command to access project logs
  -sudo chmod 666 /var/log/algosciences.log (to give read and write permissions to the file)

Restart the server when updating configs
    -sudo systemctl restart algosciences.service 
To check server status 
    -sudo systemctl status algosciences.service

if SSL is Enabled:
    -run this to test the SSL connection (the domain and port nnumer can vary)
    -openssl s_client -connect 0.0.0.0 :56747
