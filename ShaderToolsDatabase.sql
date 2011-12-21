# SQLiteManager Dump
# Version: 1.2.4
# http://www.sqlitemanager.org/
# 
# Serveur: localhost:8888
# Généré le: Tuesday 13th 2011f December 2011 09:42 am
# SQLite Version: 3.7.4
# PHP Version: 5.3.6
# Base de données: ShaderToolsDatabase.sqlite
# --------------------------------------------------------

#
# Structure de la table: ABOUT
#
CREATE TABLE 'ABOUT' (
'Abo_Index' INTEGER NOT NULL PRIMARY KEY DEFAULT '"0"',
'Abo_Name' TEXT,
'Abo_Function' TEXT,
'Abo_Web' TEXT,
'Abo_Email' TEXT ,
'Abo_Other' TEXT
);
CREATE UNIQUE INDEX ABOUT_Abo_Index ON 'ABOUT'('Abo_Index');
# --------------------------------------------------------


#
# Structure de la table: COLORS_RAMP
#
CREATE TABLE 'COLORS_RAMP' (
'Col_Index' INTEGER NOT NULL PRIMARY KEY,
'Col_Num_Material' INTEGER,
'Col_Num_Texture' INTEGER ,
'Col_Flip' BOOLEAN,
'Col_Active_color_stop' INTEGER,
'Col_Between_color_stop' TEXT(16),
'Col_Interpolation' TEXT,
'Col_Position' FLOAT,
'Col_Color_stop_one_r' FLOAT,
'Col_Color_stop_one_g' FLOAT,
'Col_Color_stop_one_b' FLOAT,
'Col_Color_stop_one_a' FLOAT,
'Col_Color_stop_two_r' FLOAT,
'Col_Color_stop_two_g' FLOAT,
'Col_Color_stop_two_b' FLOAT,
'Col_Color_stop_two_a' FLOAT,
'Col_Ramp_input' TEXT(16),
'Col_Ramp_blend' TEXT(16),
'Col_Ramp_factor' FLOAT
);
CREATE UNIQUE INDEX COLORS_RAMP_Col_Index ON 'COLORS_RAMP'('Col_Index');
# --------------------------------------------------------


#
# Structure de la table: DIFFUSE_RAMP
#
CREATE TABLE 'DIFFUSE_RAMP' (
'Dif_Index' INTEGER NOT NULL PRIMARY KEY DEFAULT '''''''"0"''''''',
'Dif_Num_material' INTEGER,
'Dif_Flip' BOOLEAN,
'Dif_Active_color_stop' INTEGER ,
'Dif_Between_color_stop' TEXT(16),
'Dif_Interpolation' TEXT,
'Dif_Position' FLOAT,
'Dif_Color_stop_one_r' FLOAT,
'Dif_Color_stop_one_g' FLOAT,
'Dif_Color_stop_one_b' FLOAT,
'Dif_Color_stop_one_a' FLOAT,
'Dif_Color_stop_two_r' FLOAT,
'Dif_Color_stop_two_g' FLOAT,
'Dif_Color_stop_two_b' FLOAT,
'Dif_Color_stop_two_a' FLOAT,
'Dif_Ramp_input' TEXT(16),
'Dif_Ramp_blend' TEXT(16),
'Dif_Ramp_factor' FLOAT
);
CREATE UNIQUE INDEX DIFFUSE_RAMP_Dif_Index ON 'DIFFUSE_RAMP'('Dif_Index');
# --------------------------------------------------------


#
# Structure de la table: IMAGE_UV
#
CREATE TABLE 'IMAGE_UV' (
'Ima_Index' INTEGER PRIMARY KEY,
'Idx_Texture' INTEGER,
'Ima_Name' TEXT,
'Ima_Source' TEXT,
'Ima_Filepath' TEXT,
'Ima_Fileformat' TEXT(16),
'Ima_Fields' BOOLEAN,
'Ima_Premultiply' BOOLEAN,
'Ima_Fields_order' TEXT(16),
'Ima_Generated_type' TEXT,
'Ima_Generated_width' INTEGER,
'Ima_Generated_height' INTEGER,
'Ima_Float_buffer' BOOLEAN,
'Ima_Blob' BLOB 
);
CREATE UNIQUE INDEX IMAGE_UV_Ima_Index ON 'IMAGE_UV'('Ima_Index');
# --------------------------------------------------------


#
# Structure de la table: INFORMATIONS
#
CREATE TABLE 'INFORMATIONS' (
'Inf_Index' INTEGER NOT NULL PRIMARY KEY,
'Inf_Creator' TEXT(64) NOT NULL DEFAULT '''""''',
'Inf_Category' TEXT(32) NOT NULL DEFAULT '''''''""''''''',
'Inf_Description' TEXT(512) NOT NULL DEFAULT '''''''''''''''""''''''''''''''',
'Inf_Weblink'  NOT NULL DEFAULT '""',
'Inf_Email' TEXT ,
'Mat_Index' INTEGER NOT NULL
);
CREATE UNIQUE INDEX INFORMATIONS_Inf_Index ON 'INFORMATIONS'('Inf_Index');
# --------------------------------------------------------


#
# Structure de la table: MATERIALS
#
CREATE TABLE 'MATERIALS' (
'Mat_Index' INTEGER NOT NULL PRIMARY KEY,
'Mat_Name' TEXT(21) NOT NULL DEFAULT '''''''""''''''',
'Mat_Type' TEXT ,
'Mat_Preview_render_type' TEXT(16) NOT NULL DEFAULT '''''''""''''''',
'Mat_diffuse_color_r' FLOAT,
'Mat_diffuse_color_g' FLOAT,
'Mat_diffuse_color_b' FLOAT,
'Mat_diffuse_color_a' FLOAT,
'Mat_diffuse_shader' TEXT(16),
'Mat_diffuse_intensity' FLOAT,
'Mat_use_diffuse_ramp' BOOLEAN,
'Mat_diffuse_roughness' FLOAT,
'Mat_diffuse_toon_size' FLOAT,
'Mat_diffuse_toon_smooth' FLOAT,
'Mat_diffuse_darkness' FLOAT,
'Mat_diffuse_fresnel' FLOAT,
'Mat_diffuse_fresnel_factor' FLOAT,
'Mat_specular_color_r' FLOAT,
'Mat_specular_color_g' FLOAT,
'Mat_specular_color_b' FLOAT,
'Mat_specular_color_a' FLOAT,
'Mat_specular_shader' TEXT,
'Mat_specular_intensity' FLOAT,
'Mat_specular_ramp' BOOLEAN,
'Mat_specular_hardness' INTEGER,
'Mat_specular_ior' FLOAT,
'Mat_specular_toon_size' FLOAT,
'Mat_specular_toon_smooth' FLOAT,
'Mat_shading_emit' FLOAT,
'Mat_shading_ambient' FLOAT,
'Mat_shading_translucency' FLOAT,
'Mat_shading_use_shadeless' BOOLEAN,
'Mat_shading_use_tangent_shading' BOOLEAN,
'Mat_shading_use_cubic' BOOLEAN,
'Mat_transparency_use_transparency' BOOLEAN,
'Mat_transparency_method' TEXT(16),
'Mat_transparency_alpha' FLOAT,
'Mat_transparency_fresnel' FLOAT,
'Mat_transparency_specular_alpha' FLOAT,
'Mat_transparency_fresnel_factor' FLOAT,
'Mat_transparency_ior' FLOAT,
'Mat_transparency_filter' FLOAT,
'Mat_transparency_falloff' FLOAT,
'Mat_transparency_depth_max' FLOAT,
'Mat_transparency_depth' INTEGER,
'Mat_transparency_gloss_factor' FLOAT,
'Mat_transparency_gloss_threshold' FLOAT,
'Mat_transparency_gloss_samples' INTEGER,
'Mat_raytracemirror_use' BOOLEAN,
'Mat_raytracemirror_reflect_factor' FLOAT,
'Mat_raytracemirror_fresnel' FLOAT,
'Mat_raytracemirror_color_r' FLOAT,
'Mat_raytracemirror_color_g' FLOAT,
'Mat_raytracemirror_color_b' FLOAT,
'Mat_raytracemirror_color_a' FLOAT,
'Mat_raytracemirror_fresnel_factor' FLOAT,
'Mat_raytracemirror_depth' INTEGER,
'Mat_raytracemirror_distance' FLOAT,
'Mat_raytracemirror_fade_to' TEXT(8),
'Mat_raytracemirror_gloss_factor' FLOAT,
'Mat_raytracemirror_gloss_threshold' FLOAT,
'Mat_raytracemirror_gloss_samples' INTEGER,
'Mat_raytracemirror_gloss_anisotropic' FLOAT,
'Mat_subsurfacescattering_use' BOOLEAN,
'Mat_subsurfacescattering_presets' TEXT,
'Mat_subsurfacescattering_ior' FLOAT,
'Mat_subsurfacescattering_scale' FLOAT,
'Mat_subsurfacescattering_color_r' FLOAT,
'Mat_subsurfacescattering_color_g' FLOAT,
'Mat_subsurfacescattering_color_b' FLOAT,
'Mat_subsurfacescattering_color_a' FLOAT,
'Mat_subsurfacescattering_color_factor' FLOAT,
'Mat_subsurfacescattering_texture_factor' FLOAT,
'Mat_subsurfacescattering_radius_one' FLOAT,
'Mat_subsurfacescattering_radius_two' FLOAT,
'Mat_subsurfacescattering_radius_three' FLOAT,
'Mat_subsurfacescattering_front' FLOAT,
'Mat_subsurfacescattering_back' FLOAT,
'Mat_subsurfacescattering_error_threshold' FLOAT,
'Mat_strand_root_size' FLOAT,
'Mat_strand_tip_size' FLOAT,
'Mat_strand_size_min' FLOAT,
'Mat_strand_blender_units' BOOLEAN,
'Mat_strand_use_tangent_shading' BOOLEAN,
'Mat_strand_shape' FLOAT,
'Mat_strand_width_fade' FLOAT,
'Mat_strand_blend_distance' FLOAT,
'Mat_options_use_raytrace' BOOLEAN,
'Mat_options_use_full_oversampling' BOOLEAN,
'Mat_options_use_sky' BOOLEAN,
'Mat_options_use_mist' BOOLEAN,
'Mat_options_invert_z' BOOLEAN,
'Mat_options_offset_z' FLOAT,
'Mat_options_use_face_texture' BOOLEAN,
'Mat_options_use_texture_alpha' BOOLEAN,
'Mat_options_use_vertex_color_paint' BOOLEAN,
'Mat_options_use_vertex_color_light' BOOLEAN,
'Mat_options_use_object_color' BOOLEAN,
'Mat_options_pass_index' INTEGER,
'Mat_shadow_use_shadows' BOOLEAN,
'Mat_shadow_use_transparent_shadows' BOOLEAN,
'Mat_shadow_use_cast_shadows_only' BOOLEAN,
'Mat_shadow_shadow_cast_alpha' FLOAT,
'Mat_shadow_use_only_shadow' BOOLEAN,
'Mat_shadow_shadow_only_type' TEXT(32),
'Mat_shadow_use_cast_buffer_shadows' BOOLEAN,
'Mat_shadow_shadow_buffer_bias' FLOAT,
'Mat_shadow_use_ray_shadow_bias' INTEGER,
'Mat_shadow_shadow_ray_bias' FLOAT,
'Mat_shadow_use_cast_approximate' INTEGER,
'Idx_ramp_diffuse' INTEGER,
'Idx_ramp_specular' INTEGER,
'Idx_textures' INTEGER
);
CREATE UNIQUE INDEX MATERIALS_Mat_Index ON 'MATERIALS'('Mat_Index');
# --------------------------------------------------------


#
# Structure de la table: POINTDENSITY_RAMP
#
CREATE TABLE 'POINTDENSITY_RAMP' (
'Poi_Index' INTEGER NOT NULL PRIMARY KEY,
'Poi_Num_Material' INTEGER,
'Poi_Num_Texture' INTEGER ,
'Poi_Flip' BOOLEAN,
'Poi_Active_color_stop' INTEGER,
'Poi_Between_color_stop' TEXT(16),
'Poi_Interpolation' TEXT,
'Poi_Position' FLOAT,
'Poi_Color_stop_one_r' FLOAT,
'Poi_Color_stop_one_g' FLOAT,
'Poi_Color_stop_one_b' FLOAT,
'Poi_Color_stop_one_a' FLOAT,
'Poi_Color_stop_two_r' FLOAT,
'Poi_Color_stop_two_g' FLOAT,
'Poi_Color_stop_two_b' FLOAT,
'Poi_Color_stop_two_a' FLOAT,
'Poi_Ramp_input' TEXT(16),
'Poi_Ramp_blend' TEXT(16),
'Poi_Ramp_factor' FLOAT
);
CREATE UNIQUE INDEX POINTDENSITY_RAMP_Poi_Index ON 'POINTDENSITY_RAMP'('Poi_Index');
# --------------------------------------------------------


#
# Structure de la table: RENDER
#
CREATE TABLE 'RENDER' (
'Ren_Index' INTEGER NOT NULL PRIMARY KEY,
'Ren_Color_Management' BOOLEAN ,
'Ren_Preview_Object' BLOB ,
'Mat_Index' INTEGER 
);
CREATE UNIQUE INDEX RENDER_Ren_Index ON 'RENDER'('Ren_Index');
# --------------------------------------------------------


#
# Structure de la table: SPECULAR_RAMP
#
CREATE TABLE 'SPECULAR_RAMP' (
'Spe_Index' INTEGER NOT NULL PRIMARY KEY DEFAULT '"0"',
'Spe_Num_Material' INTEGER,
'Spe_Flip' BOOLEAN,
'Spe_Active_color_stop' INTEGER,
'Spe_Between_color_stop' TEXT(16),
'Spe_Interpolation' TEXT ,
'Spe_Position' FLOAT,
'Spe_Color_stop_one_r' FLOAT,
'Spe_Color_stop_one_g' FLOAT,
'Spe_Color_stop_one_b' FLOAT,
'Spe_Color_stop_one_a' FLOAT,
'Spe_Color_stop_two_r' FLOAT,
'Spe_Color_stop_two_g' FLOAT,
'Spe_Color_stop_two_b' FLOAT,
'Spe_Color_stop_two_a' FLOAT,
'Spe_Ramp_input' TEXT(16),
'Spe_Ramp_blend' TEXT(16),
'Spe_Ramp_factor' FLOAT
);
CREATE UNIQUE INDEX SPECULAR_RAMP_Spe_Index ON 'SPECULAR_RAMP'('Spe_Index');
# --------------------------------------------------------


#
# Structure de la table: TEXTURES
#
CREATE TABLE 'TEXTURES' (
'Tex_Index' INTEGER NOT NULL PRIMARY KEY,
'Tex_Name' TEXT(21) NOT NULL DEFAULT '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''""''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''',
'Tex_Type' TEXT,
'Tex_Preview_type' TEXT(16),
'Tex_use_preview_alpha' BOOLEAN,
'Tex_type_blend_progression' TEXT(32),
'Tex_type_blend_use_flip_axis' TEXT,
'Tex_type_clouds_cloud_type' BOOLEAN,
'Tex_type_clouds_noise_type' TEXT,
'Tex_type_clouds_noise_basis' TEXT(32),
'Tex_type_noise_distortion' TEXT(32),
'Tex_type_env_map_source' TEXT,
'Tex_type_env_map_mapping' TEXT,
'Tex_type_env_map_clip_start' FLOAT,
'Tex_type_env_map_clip_end' FLOAT,
'Tex_type_env_map_resolution' FLOAT,
'Tex_type_env_map_depth' FLOAT,
'Tex_type_env_map_image_file' TEXT,
'Tex_type_env_map_zoom' FLOAT,
'Tex_type_magic_depth' INT,
'Tex_type_magic_turbulence' FLOAT,
'Tex_type_marble_marble_type' TEXT,
'Tex_type_marble_noise_basis_2' TEXT,
'Tex_type_marble_noise_type' TEXT,
'Tex_type_marble_noise_basis' TEXT,
'Tex_type_marble_noise_scale' FLOAT,
'Tex_type_marble_noise_depth' INTEGER,
'Tex_type_marble_turbulence' FLOAT,
'Tex_type_marble_nabla' FLOAT,
'Tex_type_musgrave_type' TEXT,
'Tex_type_musgrave_dimension_max' FLOAT,
'Tex_type_musgrave_lacunarity' FLOAT,
'Tex_type_musgrave_octaves' FLOAT,
'Tex_type_musgrave_noise_intensity' FLOAT,
'Tex_type_musgrave_noise_basis' TEXT,
'Tex_type_musgrave_noise_scale' FLOAT,
'Tex_type_musgrave_nabla' FLOAT,
'Tex_type_musgrave_offset' FLOAT,
'Tex_type_musgrave_gain' FLOAT,
'Tex_type_clouds_noise_scale' FLOAT,
'Tex_type_clouds_nabla' FLOAT,
'Tex_type_clouds_noise_depth' INTEGER,
'Tex_type_noise_distortion_distortion' FLOAT,
'Tex_type_noise_distortion_texture_distortion' FLOAT,
'Tex_type_noise_distortion_nabla' FLOAT,
'Tex_type_noise_distortion_noise_scale' FLOAT,
'Tex_type_point_density_point_source' TEXT ,
'Tex_type_point_density_radius' FLOAT,
'Tex_type_point_density_particule_cache_space' TEXT,
'Tex_type_point_density_falloff' TEXT,
'Tex_type_point_density_use_falloff_curve' BOOLEAN,
'Tex_type_point_density_falloff_soft' FLOAT,
'Tex_type_point_density_falloff_speed_scale' FLOAT,
'Tex_type_point_density_speed_scale' FLOAT,
'Tex_type_point_density_color_source' TEXT,
'Tex_type_stucci_type' TEXT,
'Tex_type_stucci_noise_type' TEXT,
'Tex_type_stucci_basis' TEXT,
'Tex_type_stucci_noise_scale' FLOAT,
'Tex_type_stucci_turbulence' FLOAT,
'Tex_type_voronoi_distance_metric' TEXT,
'Tex_type_voronoi_minkovsky_exponent' FLOAT,
'Tex_type_voronoi_color_mode' TEXT,
'Tex_type_voronoi_noise_scale' FLOAT,
'Tex_type_voronoi_nabla' FLOAT,
'Tex_type_voronoi_weight_1' FLOAT,
'Tex_type_voronoi_weight_2' FLOAT,
'Tex_type_voronoi_weight_3' FLOAT,
'Tex_type_voronoi_weight_4' FLOAT,
'Tex_type_voxel_data_file_format' TEXT,
'Tex_type_voxel_data_source_path' TEXT,
'Tex_type_voxel_data_use_still_frame' BOOLEAN,
'Tex_type_voxel_data_still_frame' INTEGER,
'Tex_type_voxel_data_interpolation' TEXT,
'Tex_type_voxel_data_extension' TEXT,
'Tex_type_voxel_data_intensity' FLOAT,
'Tex_type_voxel_data_resolution_1' INTEGER,
'Tex_type_voxel_data_resolution_2' INTEGER,
'Tex_type_voxel_data_resoltion_3' INTEGER,
'Tex_type_voxel_data_smoke_data_type' ,
'Tex_type_wood_noise_basis_2' TEXT,
'Tex_type_wood_wood_type' TEXT,
'Tex_type_wood_noise_type' BOOLEAN,
'Tex_type_wood_basis' TEXT,
'Tex_type_wood_noise_scale' FLOAT,
'Tex_type_wood_nabla' FLOAT,
'Tex_type_wood_turbulence' FLOAT,
'Tex_influence_use_map_diffuse' BOOLEAN,
'Tex_influence_use_map_color_diffuse' BOOLEAN,
'Tex_influence_use_map_alpha' BOOLEAN,
'Tex_influence_use_map_translucency' BOOLEAN,
'Tex_influence_use_map_specular' BOOLEAN,
'Tex_influence_use_map_color_spec' BOOLEAN,
'Tex_influence_use_map_map_hardness' BOOLEAN,
'Tex_influence_use_map_ambient' BOOLEAN,
'Tex_influence_use_map_emit' BOOLEAN,
'Tex_influence_use_map_mirror' BOOLEAN,
'Tex_influence_use_map_raymir' BOOLEAN,
'Tex_influence_use_map_normal' BOOLEAN,
'Tex_influence_use_map_warp' BOOLEAN,
'Tex_influence_use_map_displacement' BOOLEAN,
'Tex_influence_use_map_rgb_to_intensity' BOOLEAN,
'Tex_influence_map_invert' BOOLEAN,
'Tex_influence_use_stencil' BOOLEAN,
'Tex_influence_diffuse_factor' FLOAT,
'Tex_influence_color_factor' FLOAT,
'Tex_influence_alpha_factor' FLOAT,
'Tex_influence_translucency_factor' FLOAT,
'Tex_influence_specular_factor' FLOAT,
'Tex_influence_specular_color_factor' FLOAT,
'Tex_influence_hardness_factor' FLOAT,
'Tex_influence_ambiant_factor' FLOAT,
'Tex_influence_emit_factor' FLOAT,
'Tex_influence_mirror_factor' FLOAT,
'Tex_influence_raymir_factor' FLOAT,
'Tex_influence_normal_factor' FLOAT,
'Tex_influence_warp_factor' FLOAT,
'Tex_influence_displacement_factor' FLOAT,
'Tex_influence_default_value' FLOAT,
'Tex_influence_blend_type' TEXT,
'Tex_influence_color_r' FLOAT,
'Tex_influence_color_g' FLOAT,
'Tex_influence_color_b' FLOAT,
'Tex_influence_color_a' FLOAT,
'Tex_influence_bump_method' TEXT,
'Tex_influence_objectspace' TEXT,
'Tex_mapping_texture_coords' TEXT,
'Tex_mapping_mapping' TEXT,
'Tex_mapping_use_from_dupli' BOOLEAN,
'Tex_mapping_mapping_x' TEXT,
'Tex_mapping_mapping_y' TEXT,
'Tex_mapping_mapping_z' TEXT,
'Tex_mapping_offset_x' FLOAT,
'Tex_mapping_offset_y' FLOAT,
'Tex_mapping_offset_z' FLOAT,
'Tex_mapping_scale_x' FLOAT,
'Tex_mapping_scale_y' FLOAT,
'Tex_mapping_scale_z' FLOAT,
'Tex_colors_use_color_ramp' BOOLEAN,
'Tex_colors_factor_r' FLOAT,
'Tex_colors_factor_g' FLOAT,
'Tex_colors_factor_b' FLOAT,
'Tex_colors_intensity' FLOAT,
'Tex_colors_contrast' FLOAT,
'Tex_colors_saturation' FLOAT,
'Mat_Idx' INTEGER,
'Poi_Idx' INTEGER,
'Col_Idx' INTEGER,
'Tex_type_voronoi_intensity' FLOAT,
'Tex_mapping_use_from_original' BOOLEAN,
'Tex_type_noise_distortion_noise_distortion' TEXT,
'Tex_type_noise_distortion_basis' TEXT
);
CREATE UNIQUE INDEX TEXTURES_Tex_Index ON 'TEXTURES'('Tex_Index');
# --------------------------------------------------------


#
# Structure de la table: VERSION
#
CREATE TABLE 'VERSION' (
'APP_VERSION' FLOAT,
'BLENDER_VERSION' FLOAT,
'BASE_VERSION' FLOAT 
);
# --------------------------------------------------------

