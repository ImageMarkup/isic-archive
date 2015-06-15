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

  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "ansible/vagrant-playbook.yml"
    # ansible.extra_vars
  end

  config.vm.provider "virtualbox" do |virtualbox|
    virtualbox.name = "isic-archive.dev"
  end

  config.ssh.forward_agent = true
end
