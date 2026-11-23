# Ansible Playbook ile Sunucu Yapılandırma Otomasyonu

Ansible, agent gerektirmeyen (agentless), SSH üzerinden çalışan altyapı otomasyon aracıdır.

## 1. Nginx ve Docker Kurulum Playbook'u

```yaml
---
- name: Web Sunucularını Hazırla
  hosts: webservers
  become: yes

  tasks:
    - name: Paket yöneticisini güncelle
      apt:
        update_cache: yes
        cache_valid_time: 3600

    - name: Gerekli paketleri kur
      apt:
        name:
          - curl
          - git
          - nginx
          - docker.io
        state: present

    - name: Docker servisini başlat ve enable et
      systemd:
        name: docker
        state: started
        enabled: yes

    - name: Nginx servisini başlat
      systemd:
        name: nginx
        state: started
        enabled: yes
```

```bash
# Playbook çalıştırma komutu
ansible-playbook -i inventory.ini site.yml
```
