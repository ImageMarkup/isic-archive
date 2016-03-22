# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/trusty64"

  config.vm.hostname = "isic-archive.dev"

  # config.vm.network "forwarded_port", guest: 80, host: 8080
  PRIVATE_IP = "172.28.128.100"
  config.vm.network "private_network", ip: PRIVATE_IP
  # config.vm.network "private_network", type: "dhcp"
  config.vm.post_up_message = "Web server is running at http://#{PRIVATE_IP}"

  config.vm.synced_folder ".", "/home/vagrant/isic_archive"
  config.vm.synced_folder ".", "/vagrant", disabled: true
  config.vm.synced_folder "../..", "/home/vagrant/girder"

  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "ansible/vagrant-playbook.yml"
    # Ansible has a bug where the "--module-path" option is not respected
    # ansible.raw_arguments = ["--module-path=" + File.expand_path("ansible/library")]
    ENV["ANSIBLE_LIBRARY"] = File.expand_path("ansible/library")
  end

  config.vm.provider "virtualbox" do |virtualbox|
    virtualbox.name = "isic-archive.dev"
    virtualbox.memory = 1024
  end

  config.ssh.forward_agent = true
  config.ssh.forward_x11 = true
end
