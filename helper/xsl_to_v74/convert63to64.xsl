<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv63to64">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv63to64"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>6.3</literal> to <literal>6.4</literal>.
</para>
<xsl:template match="image" mode="conv63to64">
    <xsl:choose>
        <!-- nothing to do if already at 6.4 -->
        <xsl:when test="@schemaversion > 6.3">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="6.4">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv63to64"/>  
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv63to64">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv63to64"/>
    </xsl:copy>
</xsl:template>

<para xmlns="http://docbook.org/ns/docbook">
    Remove obsolete group and id attribute from users
</para>
<xsl:template match="users" mode="conv63to64">
    <users>
        <xsl:copy-of select="@*[not(local-name(.) = 'group') and not(local-name(.) = 'id')]"/>
        <xsl:apply-templates mode="conv63to64"/>
    </users>
</xsl:template>

<para xmlns="http://docbook.org/ns/docbook">
    Move global group attribute as groups to user section(s)
</para>
<xsl:template match="user" mode="conv63to64">
    <user>
        <xsl:variable name="group_name" select="../@group"/>
        <xsl:copy-of select="@*"/>
        <xsl:if test="$group_name">
            <xsl:attribute name="groups">
                <xsl:value-of select="$group_name"/>
            </xsl:attribute>
        </xsl:if>
        <xsl:apply-templates mode="conv63to64"/>
    </user>
</xsl:template>

</xsl:stylesheet>
