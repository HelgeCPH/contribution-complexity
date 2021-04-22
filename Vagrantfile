# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = 'digital_ocean'
  config.vm.box_url = "https://github.com/devopsgroup-io/vagrant-digitalocean/raw/master/box/digital_ocean.box"
  config.ssh.private_key_path = '~/.ssh/id_rsa'

  config.vm.define "concomserver", primary: true do |server|
    server.vm.provider :digital_ocean do |provider|
      provider.ssh_key_name = ENV["SSH_KEY_NAME"]
      provider.token = ENV["DIGITAL_OCEAN_TOKEN"]
      provider.image = 'ubuntu-18-04-x64'
      provider.region = 'fra1'
      provider.size = 's-1vcpu-1gb'
    end

    server.vm.synced_folder ".", "/vagrant", type: "rsync"
    server.vm.hostname = "concomserver"
    server.vm.provision "shell", privileged: true, inline: <<-SHELL

      apt update -y
      apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
                     libreadline-dev libsqlite3-dev wget curl llvm \
                     libncurses5-dev libncursesw5-dev xz-utils tk-dev \
                     libffi-dev liblzma-dev python-openssl git

      git clone https://github.com/pyenv/pyenv.git ~/.pyenv

      echo ". $HOME/.bashrc" >> $HOME/.bash_profile
      echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
      echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
      echo 'export GITHUB_API_KEY="<PUT_YOUR_KEY_HERE>"' >> ~/.bashrc   

      source ~/.bashrc
      
      eval "$(pyenv init -)"
      pyenv install 3.9.4
      pyenv global 3.9.4

      # Install Poetry
      curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
      source $HOME/.poetry/env

      # poetry shell
      cd /vagrant/ 
      poetry install
      poetry shell
      # nohup ../experiment/run_experiment.sh > /tmp/experiment.log 2>&1 &

      echo "Experiment replication started..."
      echo "This will take multiple hours to complete."

      echo "==================================================================="
      echo "=                             DONE                                ="
      echo "==================================================================="
      THIS_IP=`hostname -I | cut -d" " -f1`        
      echo "Machine: `hostname` has IP address: ${THIS_IP}"
      echo "To log onto the VM:"
      echo "$ vagrant ssh [machinename]"
    SHELL
  end
end
