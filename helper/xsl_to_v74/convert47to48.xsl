<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xsl:stylesheet [
    <!ENTITY lowercase "'abcdefghijklmnopqrstuvwxyz'">
    <!ENTITY uppercase "'ABCDEFGHIJKLMNOPQRSTUVWXYZ'">
]>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
    indent="yes" omit-xml-declaration="no" encoding="utf-8"/>
<xsl:strip-space elements="type"/>

<!-- create systemdisk element with optional home volume if oem-home is set -->
<xsl:template name="add-systemdisk" mode="conv47to48">
    <xsl:param name="content"/>
    <xsl:param name="lvm"/>
    <xsl:choose>
        <xsl:when test="$content = 'true'">
            <systemdisk name="kiwiVG">
                <volume name="/home" freespace="200M"/>
            </systemdisk>
        </xsl:when>
        <xsl:otherwise>
            <xsl:choose>
                <xsl:when test="$lvm = 'true'">
                    <systemdisk name="kiwiVG"/>
                </xsl:when>
            </xsl:choose>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- default rule conv47to48 -->
<xsl:template match="*" mode="conv47to48">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv47to48"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>4.7</literal> to <literal>4.8</literal>.
</para>
<xsl:template match="image" mode="conv47to48">
    <xsl:choose>
        <!-- nothing to do if already at 4.8 -->
        <xsl:when test="@schemaversion > 4.7">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="4.8">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates mode="conv47to48"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv47to48">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv47to48"/>
    </xsl:copy>
</xsl:template>

<!-- remove lvm attribute, call add-systemdisk if no lvmvolumes exists and
     either lvm is enabled or oem-home exists and set to true in oemconfig 
     if lvmvolumes exists and there is oem-home enabled too, add a home
         volume in the existing lvmvolumes section -->
<xsl:template match="type" mode="conv47to48">
    <type>
        <xsl:copy-of select="@*[not(local-name(.) = 'lvm')]"/>
        <xsl:choose>
            <xsl:when test="lvmvolumes">
                <xsl:variable name="content"
                    select="translate(normalize-space(oemconfig/oem-home), 
                            &uppercase;, &lowercase;)"
                />
                <xsl:choose>
                    <xsl:when test="$content = 'true'">
                        <xsl:apply-templates
                            select="*[not(self::lvmvolumes)]" mode="conv47to48"
                        />
                        <xsl:apply-templates select="lvmvolumes"
                            mode="mode-volumes"
                        />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:apply-templates mode="conv47to48"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="add-systemdisk">
                    <xsl:with-param name="lvm" select="@lvm"/>
                    <xsl:with-param name="content" select="oemconfig/oem-home"/>
                </xsl:call-template>
                <xsl:apply-templates mode="conv47to48"/>
            </xsl:otherwise>
        </xsl:choose>
    </type>
</xsl:template>

<!-- add home volume in mode-volumes, see type template -->
<xsl:template match="lvmvolumes" mode="mode-volumes">
    <systemdisk>
        <xsl:copy-of select="@*"/>
        <volume name="/home" freespace="200M"/>
        <xsl:apply-templates mode="conv47to48"/>
    </systemdisk>
</xsl:template>

<!-- turn existing lvmvolumes into systemdisk -->
<xsl:template match="lvmvolumes" mode="conv47to48">
    <systemdisk>
        <xsl:copy-of select="@*[not(local-name(.) = 'lvmgroup')]"/>
        <xsl:variable name="groupname" select="@lvmgroup"/>
        <xsl:choose>
            <xsl:when test="@lvmgroup!=''">
                <xsl:attribute name="name">
                    <xsl:value-of select="$groupname"/>
                </xsl:attribute>
            </xsl:when>
        </xsl:choose>
        <xsl:apply-templates mode="conv47to48"/>
    </systemdisk>
</xsl:template>

<!-- remove oem-home -->
<xsl:template match="oemconfig/oem-home" mode="conv47to48">
</xsl:template>

</xsl:stylesheet>
