-- O dono isolado da view pública precisa ler apenas o contrato interno de
-- boxes comerciais que alimenta a tela. Nenhuma tabela privada é concedida.

grant select on clube_novo.carta_box_oferta_v1 to clube_frontend_view_owner;
